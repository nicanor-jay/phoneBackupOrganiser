"""
Automatic phone -> PC media backup over ADB.

Run with --watch (what the Startup shortcut does) to sit in the background and
back up the phone every time it is plugged in. Files are only ever copied off
the phone, never deleted from it, and are filed into the same year/month
folders the old organiser used.

    python phone_backup.py --watch     # background watcher
    python phone_backup.py --once      # back up whatever is plugged in now
    python phone_backup.py --dry-run   # show what would be copied
"""
import argparse
import ctypes
import json
import logging
import os
import re
import shlex
import shutil
import sqlite3
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from logging.handlers import RotatingFileHandler

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(HERE, "config.json")
LOG_PATH = os.path.join(HERE, "logs", "phone_backup.log")
LAST_BACKUP_PATH = os.path.join(HERE, "logs", "last_backup.json")
MANIFEST_NAME = ".phone_backup.db"
WATCHER_MUTEX = "Local\\PhotoOrganiserPhoneBackupWatcher"
BACKUP_MUTEX = "Local\\PhotoOrganiserPhoneBackupRunning"
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

# Matches the date in names like PXL_20260319_191242168.jpg, IMG-20250101-WA0000.jpg,
# Screenshot_20260101-120000.png and 2026-01-03-183459016.mp4
DATE_IN_NAME = re.compile(r"(?<!\d)((?:19|20)\d{2})[-_]?(0[1-9]|1[0-2])[-_]?(0[1-9]|[12]\d|3[01])")

log = logging.getLogger("phone_backup")


@dataclass
class RemoteFile:
    path: str
    size: int
    mtime: int

    @property
    def name(self):
        return self.path.rsplit("/", 1)[-1]


# ---------------------------------------------------------------- setup

def load_config():
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_config(config):
    tmp = CONFIG_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)
    os.replace(tmp, CONFIG_PATH)


def mutex_exists(name):
    kernel32 = ctypes.windll.kernel32
    kernel32.OpenMutexW.restype = ctypes.c_void_p
    handle = kernel32.OpenMutexW(0x00100000, False, name)  # SYNCHRONIZE
    if handle:
        kernel32.CloseHandle(ctypes.c_void_p(handle))
    return bool(handle)


def watcher_running():
    return mutex_exists(WATCHER_MUTEX)


def last_backup():
    """{'when': ..., 'summary': ...} for the most recent real backup, or None."""
    try:
        with open(LAST_BACKUP_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def record_last_backup(model, summary):
    with open(LAST_BACKUP_PATH, "w", encoding="utf-8") as f:
        json.dump({"when": datetime.now().strftime("%d %b %Y, %H:%M"), "model": model, "summary": summary}, f)


def setup_logging(verbose):
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    fileHandler = RotatingFileHandler(LOG_PATH, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    fileHandler.setFormatter(fmt)
    log.addHandler(fileHandler)
    if sys.stdout:  # pythonw has no console
        consoleHandler = logging.StreamHandler(sys.stdout)
        consoleHandler.setFormatter(fmt)
        log.addHandler(consoleHandler)
    log.setLevel(logging.DEBUG if verbose else logging.INFO)


def find_adb(configured):
    if configured and configured != "auto":
        return configured
    candidates = [
        shutil.which("adb"),
        os.path.expandvars(r"%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe"),
    ]
    for candidate in candidates:
        if candidate and os.path.isfile(candidate):
            return candidate
    raise FileNotFoundError("adb not found - set adb_path in config.json")


def notify(config, title, message):
    """Windows toast notification via PowerShell's WinRT bindings (no extra installs)."""
    log.info("%s: %s", title, message)
    if not config.get("notifications", True):
        return
    esc = lambda s: s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("'", "''")
    script = f"""
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
$xml.LoadXml('<toast><visual><binding template="ToastGeneric"><text>{esc(title)}</text><text>{esc(message)}</text></binding></visual></toast>')
$appId = '{{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}}\\WindowsPowerShell\\v1.0\\powershell.exe'
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($appId).Show([Windows.UI.Notifications.ToastNotification]::new($xml))
"""
    try:
        subprocess.Popen(["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
                         creationflags=NO_WINDOW)
    except OSError:
        log.exception("Could not show notification")


# ---------------------------------------------------------------- adb

class Adb:
    def __init__(self, exe):
        self.exe = exe

    def run(self, *args, serial=None, check=True, timeout=None):
        cmd = [self.exe] + (["-s", serial] if serial else []) + list(args)
        result = subprocess.run(cmd, capture_output=True, creationflags=NO_WINDOW, timeout=timeout)
        if check and result.returncode != 0:
            raise RuntimeError(f"{' '.join(cmd)} failed: {result.stderr.decode(errors='replace').strip()}")
        return result.stdout.decode("utf-8", errors="replace")

    def devices(self):
        """{serial: state} where state is 'device', 'unauthorized', 'offline', ..."""
        out = self.run("devices", check=False, timeout=30)
        found = {}
        for line in out.splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 2:
                found[parts[0]] = parts[1]
        return found

    def model(self, serial):
        return self.run("shell", "getprop ro.product.model", serial=serial).strip() or serial

    def list_files(self, serial, folder):
        """Every non-hidden file under folder, with size and modification time."""
        # '|' separates fields; the path goes last so spaces in it are harmless
        remoteCmd = (f"[ -d {shlex.quote(folder)} ] && "
                     f"find {shlex.quote(folder)} -type f -exec stat -c '%s|%Y|%n' {{}} +")
        out = self.run("exec-out", remoteCmd, serial=serial, check=False)
        files = []
        for line in out.splitlines():
            parts = line.strip().split("|", 2)
            if len(parts) != 3 or not parts[0].isdigit():
                continue
            size, mtime, path = parts
            relative = path[len(folder):]
            # Skip .trashed-*, .pending-*, .thumbnails, WhatsApp .Statuses etc.
            if any(part.startswith(".") for part in relative.split("/") if part):
                continue
            files.append(RemoteFile(path, int(size), int(mtime)))
        return files

    def pull(self, serial, remotePath, localPath):
        self.run("pull", "-a", remotePath, localPath, serial=serial)


# ---------------------------------------------------------------- organising

def human_size(numBytes):
    return f"{numBytes / 1e9:.1f} GB" if numBytes >= 1e9 else f"{numBytes / 1e6:.0f} MB"


def date_for(remoteFile):
    """Date from the filename (how the old organiser did it), falling back to the file's timestamp."""
    match = DATE_IN_NAME.search(remoteFile.name)
    if match:
        year, month, day = map(int, match.groups())
        try:
            return datetime(year, month, day)
        except ValueError:
            pass
    return datetime.fromtimestamp(remoteFile.mtime)


def destination_folder(config, when):
    layout = config.get("folder_layout", "{year}\\{year}-{month}")
    return os.path.join(config["destination"], layout.format(year=when.year, month=f"{when.month:02d}"))


def pick_local_path(folder, name, size):
    """Returns (path, alreadyThere). Same name + same size counts as already backed up;
    a same-named file with a different size gets saved alongside as 'name (1).ext'."""
    stem, ext = os.path.splitext(name)
    candidate = os.path.join(folder, name)
    n = 0
    while os.path.exists(candidate):
        if os.path.getsize(candidate) == size:
            return candidate, True
        n += 1
        candidate = os.path.join(folder, f"{stem} ({n}){ext}")
    return candidate, False


class Manifest:
    """Remembers what has been copied, so files you later tidy away or delete
    on the PC don't get pulled off the phone again."""

    def __init__(self, destination):
        os.makedirs(destination, exist_ok=True)
        self.db = sqlite3.connect(os.path.join(destination, MANIFEST_NAME))
        self.db.execute("""CREATE TABLE IF NOT EXISTS copied (
            serial TEXT, remote_path TEXT, size INTEGER, local_path TEXT, copied_at TEXT,
            PRIMARY KEY (serial, remote_path, size))""")

    def has(self, serial, remoteFile):
        return self.db.execute("SELECT 1 FROM copied WHERE serial=? AND remote_path=? AND size=?",
                               (serial, remoteFile.path, remoteFile.size)).fetchone() is not None

    def add(self, serial, remoteFile, localPath):
        self.db.execute("INSERT OR REPLACE INTO copied VALUES (?, ?, ?, ?, ?)",
                        (serial, remoteFile.path, remoteFile.size, localPath, datetime.now().isoformat()))
        self.db.commit()

    def close(self):
        self.db.close()


# ---------------------------------------------------------------- backup

class BackupLock:
    """Cross-process lock so the background watcher and the GUI never copy at the same time."""

    def __enter__(self):
        kernel32 = ctypes.windll.kernel32
        kernel32.CreateMutexW.restype = ctypes.c_void_p
        self.handle = kernel32.CreateMutexW(None, False, BACKUP_MUTEX)
        # WAIT_OBJECT_0 or WAIT_ABANDONED (a previous run crashed) both mean we own it
        self.acquired = kernel32.WaitForSingleObject(ctypes.c_void_p(self.handle), 0) in (0, 0x80)
        return self

    def __exit__(self, *exc):
        kernel32 = ctypes.windll.kernel32
        if self.acquired:
            kernel32.ReleaseMutex(ctypes.c_void_p(self.handle))
        kernel32.CloseHandle(ctypes.c_void_p(self.handle))


def backup_device(adb, config, serial, dryRun=False, progress=None, cancel=None):
    """Copies new files off the phone. Returns a one-line summary.

    progress(done, total, message) is called as it goes, and setting the
    cancel Event stops it cleanly between files."""
    progress = progress or (lambda done, total, message: None)
    cancelled = lambda: cancel is not None and cancel.is_set()
    model = adb.model(serial)
    sources = [s for s in config["sources"] if s.get("enabled")]
    log.info("Backing up %s (%s) from: %s", model, serial, ", ".join(s["name"] for s in sources))

    if not os.path.isdir(os.path.splitdrive(config["destination"])[0] + os.sep):
        summary = f"Backup drive for {config['destination']} is not available."
        notify(config, "Phone backup skipped", summary)
        return summary

    with BackupLock() as lock:
        if not lock.acquired:
            summary = "Another backup is already running."
            log.info(summary)
            return summary
        manifest = Manifest(config["destination"])
        try:
            return _backup(adb, config, serial, model, sources, manifest, dryRun, progress, cancelled)
        finally:
            manifest.close()


def _backup(adb, config, serial, model, sources, manifest, dryRun, progress, cancelled):
    start = time.time()

    # Phase 1: work out what's new
    toCopy, alreadyBackedUp = [], 0
    for source in sources:
        progress(0, 0, f"Scanning {source['name']}...")
        files = adb.list_files(serial, source["path"])
        log.info("%s: %d files on phone", source["name"], len(files))
        for remoteFile in sorted(files, key=lambda f: f.path):
            if manifest.has(serial, remoteFile):
                alreadyBackedUp += 1
                continue
            folder = destination_folder(config, date_for(remoteFile))
            localPath, alreadyThere = pick_local_path(folder, remoteFile.name, remoteFile.size)
            if alreadyThere:
                if not dryRun:
                    manifest.add(serial, remoteFile, localPath)
                alreadyBackedUp += 1
            else:
                toCopy.append((remoteFile, localPath))

    totalBytes = sum(remoteFile.size for remoteFile, _ in toCopy)
    if dryRun:
        for remoteFile, localPath in toCopy:
            log.info("would copy %s -> %s", remoteFile.path, localPath)
        summary = (f"{len(toCopy)} new files to copy ({human_size(totalBytes)}), "
                   f"{alreadyBackedUp} already backed up")
        progress(1, 1, summary)
        log.info(summary)
        return summary

    # Phase 2: copy them
    copied, copiedBytes, failed = 0, 0, []
    for i, (remoteFile, localPath) in enumerate(toCopy):
        if cancelled():
            log.info("Cancelled")
            break
        progress(copiedBytes, totalBytes, f"Copying {i + 1} of {len(toCopy)}: {remoteFile.name}")
        folder = os.path.dirname(localPath)
        os.makedirs(folder, exist_ok=True)
        # Pull to a temp name first so an unplug mid-copy never leaves a half file
        partial = localPath + ".partial"
        try:
            adb.pull(serial, remoteFile.path, partial)
            if os.path.getsize(partial) != remoteFile.size:
                raise IOError(f"size mismatch ({os.path.getsize(partial)} != {remoteFile.size})")
            os.replace(partial, localPath)
        except Exception as e:
            log.error("Failed %s: %s", remoteFile.path, e)
            failed.append(remoteFile.path)
            if os.path.exists(partial):
                os.remove(partial)
            if serial not in adb.devices():
                log.warning("Phone disconnected - stopping")
                break
            continue
        manifest.add(serial, remoteFile, localPath)
        copied += 1
        copiedBytes += remoteFile.size
        log.debug("copied %s -> %s", remoteFile.path, localPath)

    summary = f"{copied} new files copied ({human_size(copiedBytes)}), {alreadyBackedUp} already backed up"
    if copied + len(failed) < len(toCopy):
        summary += f", {len(toCopy) - copied - len(failed)} left for next time"
    if failed:
        summary += f", {len(failed)} failed (see log)"
    progress(1, 1, summary)
    log.info("%s in %.0fs", summary, time.time() - start)
    record_last_backup(model, summary)
    notify(config, f"{model} backup {'finished with errors' if failed else 'complete'}", summary)
    return summary


def watch(adb, config):
    """Poll adb for phones; back each one up once per plug-in."""
    handled = set()   # serials already backed up during this connection
    warned = set()    # serials we've already told to authorise
    log.info("Watching for phones (every %ss)", config.get("poll_seconds", 5))
    while True:
        try:
            devices = adb.devices()
        except Exception:
            log.exception("adb devices failed")
            devices = {}

        for serial, state in devices.items():
            if state == "device" and serial not in handled:
                handled.add(serial)
                notify(config, "Phone connected", "Backing up new photos & videos...")
                try:
                    config = load_config()  # pick up changes made in the GUI
                    backup_device(adb, config, serial)
                except Exception as e:
                    log.exception("Backup failed")
                    notify(config, "Phone backup failed", str(e))
            elif state == "unauthorized" and serial not in warned:
                warned.add(serial)
                notify(config, "Allow USB debugging", "Unlock your phone and tap 'Allow' to let this PC back it up.")

        # Forget unplugged phones so the next plug-in triggers a fresh backup
        handled &= {s for s, st in devices.items() if st == "device"}
        warned &= set(devices)
        time.sleep(config.get("poll_seconds", 5))


def single_instance():
    """Stop a second watcher starting (e.g. if the Startup shortcut runs twice)."""
    ctypes.windll.kernel32.CreateMutexW(None, False, WATCHER_MUTEX)
    return ctypes.windll.kernel32.GetLastError() != 183  # ERROR_ALREADY_EXISTS


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--watch", action="store_true", help="run in the background, backing up on every plug-in")
    mode.add_argument("--once", action="store_true", help="back up connected phones now (default)")
    parser.add_argument("--dry-run", action="store_true", help="list what would be copied without copying")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    setup_logging(args.verbose)
    config = load_config()
    adb = Adb(find_adb(config.get("adb_path")))

    if args.watch:
        if not single_instance():
            log.info("Watcher already running - exiting")
            return
        watch(adb, config)
        return

    phones = [s for s, state in adb.devices().items() if state == "device"]
    if not phones:
        log.info("No authorised phone connected (check USB debugging is on and allowed)")
    for serial in phones:
        backup_device(adb, config, serial, dryRun=args.dry_run)


if __name__ == "__main__":
    main()
