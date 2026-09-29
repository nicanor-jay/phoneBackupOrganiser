"""
Control panel for the automatic phone backup. Double-click to open.

Everything here is saved straight into config.json, which the background
watcher re-reads before each backup, so changes take effect immediately.
"""
import os
import queue
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import phone_backup as pb

HERE = os.path.dirname(os.path.abspath(__file__))
INSTALLER = os.path.join(HERE, "install_startup.ps1")
STARTUP_SHORTCUT = os.path.join(os.environ["APPDATA"], r"Microsoft\Windows\Start Menu\Programs\Startup",
                                "Phone Backup Watcher.lnk")
LAYOUTS = {"{year}\\{year}-{month}": "Year folders  (2026 \\ 2026-09)",
           "{year}-{month}": "Month folders only  (2026-09)"}

SETUP_STEPS = """To let this PC read your phone (one time only):

1.  On your phone open  Settings → About phone
     and tap  Build number  7 times.

2.  Go to  Settings → System → Developer options
     and turn on  USB debugging.

3.  Plug the phone into this PC, unlock it, and tap  Allow
     (tick "Always allow from this computer").

That's it — the status at the top of this window will turn green."""


class BackupApp:

    def __init__(self):
        pb.setup_logging(verbose=False)
        self.config = pb.load_config()
        self.events = queue.Queue()      # messages from background threads -> UI
        self.cancel = threading.Event()
        self.busy = False
        self.connected = None            # (serial, model) of an authorised phone

        try:
            self.adb = pb.Adb(pb.find_adb(self.config.get("adb_path")))
        except FileNotFoundError:
            self.adb = None

        self.root = tk.Tk()
        self.root.title("Phone Backup")
        self.root.resizable(False, False)
        self.build()
        self.root.after(100, self.drain_events)
        threading.Thread(target=self.poll_devices, daemon=True).start()
        self.root.mainloop()

    # ------------------------------------------------------------ layout

    def build(self):
        pad = {"padx": 10, "pady": 4}
        body = ttk.Frame(self.root, padding=12)
        body.grid(sticky="nsew")

        # Phone status
        statusFrame = ttk.Frame(body)
        statusFrame.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        self.statusDot = tk.Label(statusFrame, text="●", font=("Segoe UI", 16), fg="grey")
        self.statusDot.grid(row=0, column=0, rowspan=2, padx=(0, 8))
        self.statusText = ttk.Label(statusFrame, text="Looking for your phone...", font=("Segoe UI", 12, "bold"))
        self.statusText.grid(row=0, column=1, sticky="w")
        self.statusHint = ttk.Label(statusFrame, text="", foreground="grey")
        self.statusHint.grid(row=1, column=1, sticky="w")
        ttk.Button(statusFrame, text="Phone setup help", command=self.show_setup_help).grid(
            row=0, column=2, rowspan=2, sticky="e")
        statusFrame.columnconfigure(1, weight=1)

        # Destination
        destFrame = ttk.LabelFrame(body, text="Save backups to", padding=6)
        destFrame.grid(row=1, column=0, sticky="ew", pady=4)
        self.destination = tk.StringVar(value=self.config["destination"])
        ttk.Entry(destFrame, textvariable=self.destination, width=46, state="readonly").grid(row=0, column=0, **pad)
        ttk.Button(destFrame, text="Change...", command=self.choose_destination).grid(row=0, column=1)
        ttk.Button(destFrame, text="Open", command=lambda: self.open_path(self.config["destination"])).grid(
            row=0, column=2, padx=(4, 10))
        self.layout = tk.StringVar(value=self.config.get("folder_layout", "{year}\\{year}-{month}"))
        for i, (value, label) in enumerate(LAYOUTS.items()):
            ttk.Radiobutton(destFrame, text=label, value=value, variable=self.layout,
                            command=self.save_settings).grid(row=1 + i, column=0, columnspan=3, sticky="w", padx=10)

        # Sources
        sourceFrame = ttk.LabelFrame(body, text="What to back up", padding=6)
        sourceFrame.grid(row=2, column=0, sticky="ew", pady=4)
        self.sourceVars = []
        for i, source in enumerate(self.config["sources"]):
            var = tk.BooleanVar(value=source.get("enabled", False))
            self.sourceVars.append(var)
            ttk.Checkbutton(sourceFrame, text=source["name"], variable=var, command=self.save_settings).grid(
                row=i // 2, column=i % 2, sticky="w", padx=10, pady=2)
        sourceFrame.columnconfigure((0, 1), weight=1)

        # Automatic backup
        autoFrame = ttk.LabelFrame(body, text="Automatic backup", padding=6)
        autoFrame.grid(row=3, column=0, sticky="ew", pady=4)
        self.autoBackup = tk.BooleanVar(value=os.path.exists(STARTUP_SHORTCUT))
        ttk.Checkbutton(autoFrame, text="Back up automatically whenever my phone is plugged in",
                        variable=self.autoBackup, command=self.toggle_auto).grid(row=0, column=0, sticky="w", padx=10)
        self.watcherStatus = ttk.Label(autoFrame, text="", foreground="grey")
        self.watcherStatus.grid(row=1, column=0, sticky="w", padx=30)
        self.notifications = tk.BooleanVar(value=self.config.get("notifications", True))
        ttk.Checkbutton(autoFrame, text="Show Windows notifications", variable=self.notifications,
                        command=self.save_settings).grid(row=2, column=0, sticky="w", padx=10, pady=(4, 0))
        self.lastBackup = ttk.Label(autoFrame, text="", foreground="grey")
        self.lastBackup.grid(row=3, column=0, sticky="w", padx=10, pady=(4, 0))

        # Actions + progress
        actionFrame = ttk.Frame(body)
        actionFrame.grid(row=4, column=0, sticky="ew", pady=(10, 0))
        self.previewButton = ttk.Button(actionFrame, text="Preview", command=lambda: self.start_backup(True))
        self.previewButton.grid(row=0, column=0)
        self.backupButton = ttk.Button(actionFrame, text="Back up now", command=lambda: self.start_backup(False))
        self.backupButton.grid(row=0, column=1, padx=6)
        self.cancelButton = ttk.Button(actionFrame, text="Cancel", command=self.cancel.set, state="disabled")
        self.cancelButton.grid(row=0, column=2)
        ttk.Button(actionFrame, text="View log", command=lambda: self.open_path(pb.LOG_PATH)).grid(
            row=0, column=3, sticky="e")
        actionFrame.columnconfigure(3, weight=1)

        self.progress = ttk.Progressbar(body, length=460, mode="determinate", maximum=1)
        self.progress.grid(row=5, column=0, sticky="ew", pady=(8, 2))
        self.progressText = ttk.Label(body, text="", wraplength=460)
        self.progressText.grid(row=6, column=0, sticky="w")

        self.refresh_buttons()
        self.refresh_watcher_status()

    # ------------------------------------------------------------ settings

    def save_settings(self):
        self.config["destination"] = self.destination.get()
        self.config["folder_layout"] = self.layout.get()
        self.config["notifications"] = self.notifications.get()
        for source, var in zip(self.config["sources"], self.sourceVars):
            source["enabled"] = var.get()
        pb.save_config(self.config)
        self.refresh_buttons()

    def choose_destination(self):
        folder = filedialog.askdirectory(initialdir=self.config["destination"], title="Save backups to")
        if folder:
            self.destination.set(os.path.normpath(folder))
            self.save_settings()

    def toggle_auto(self):
        args = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", INSTALLER]
        if not self.autoBackup.get():
            args.append("-Uninstall")
        result = subprocess.run(args, capture_output=True, text=True, creationflags=pb.NO_WINDOW)
        if result.returncode != 0:
            messagebox.showerror("Phone Backup", "Couldn't change automatic backup:\n\n" + result.stderr.strip())
        self.autoBackup.set(os.path.exists(STARTUP_SHORTCUT))
        self.root.after(1500, self.refresh_watcher_status)

    # ------------------------------------------------------------ status

    def poll_devices(self):
        """Background thread: report phone connection state every few seconds."""
        while True:
            if self.adb is None:
                self.events.put(("device", "noadb", None))
                return
            try:
                devices = self.adb.devices()
                ready = [s for s, state in devices.items() if state == "device"]
                if ready:
                    self.events.put(("device", "ready", (ready[0], self.adb.model(ready[0]))))
                elif "unauthorized" in devices.values():
                    self.events.put(("device", "unauthorized", None))
                elif devices:
                    self.events.put(("device", "offline", None))
                else:
                    self.events.put(("device", "none", None))
            except Exception as e:
                pb.log.debug("device poll failed: %s", e)
            threading.Event().wait(3)

    def show_device_state(self, state, info):
        self.connected = info if state == "ready" else None
        text, hint, colour = {
            "ready": (f"{info[1]} connected" if info else "", "Ready to back up.", "#1a9e3a"),
            "unauthorized": ("Phone needs your permission", "Unlock your phone and tap Allow on the USB debugging prompt.", "#d98c00"),
            "offline": ("Phone not responding", "Try unplugging and plugging it back in.", "#d98c00"),
            "none": ("No phone connected", "Plug in your phone with a USB cable. First time? See Phone setup help.", "grey"),
            "noadb": ("Android tools not found", "Install Android platform-tools, or set adb_path in config.json.", "#c62828"),
        }[state]
        self.statusDot.configure(fg=colour)
        self.statusText.configure(text=text)
        self.statusHint.configure(text=hint)
        self.refresh_buttons()
        self.refresh_watcher_status()

    def refresh_watcher_status(self):
        if pb.mutex_exists(pb.BACKUP_MUTEX) and not self.busy:
            text = "Backing up in the background right now..."
        elif pb.watcher_running():
            text = "On — running in the background."
        elif self.autoBackup.get():
            text = "Set to start when you log in, but not running right now."
        else:
            text = "Off — use Back up now instead."
        self.watcherStatus.configure(text=text)
        last = pb.last_backup()
        self.lastBackup.configure(text=f"Last backup: {last['when']} — {last['summary']}" if last else "")

    def refresh_buttons(self):
        anySource = any(var.get() for var in getattr(self, "sourceVars", []))
        ready = self.connected is not None and anySource and not self.busy
        self.previewButton.configure(state="normal" if ready else "disabled")
        self.backupButton.configure(state="normal" if ready else "disabled")
        self.cancelButton.configure(state="normal" if self.busy else "disabled")

    # ------------------------------------------------------------ backup

    def start_backup(self, dryRun):
        self.busy = True
        self.cancel.clear()
        self.refresh_buttons()
        self.progress.configure(mode="indeterminate")
        self.progress.start(15)
        serial = self.connected[0]
        threading.Thread(target=self.run_backup, args=(serial, dryRun), daemon=True).start()

    def run_backup(self, serial, dryRun):
        report = lambda done, total, message: self.events.put(("progress", (done, total), message))
        try:
            summary = pb.backup_device(self.adb, dict(self.config), serial, dryRun=dryRun,
                                       progress=report, cancel=self.cancel)
            self.events.put(("done", dryRun, summary))
        except Exception as e:
            pb.log.exception("Backup failed")
            self.events.put(("done", dryRun, f"Backup failed: {e}"))

    def drain_events(self):
        try:
            while True:
                kind, a, b = self.events.get_nowait()
                if kind == "device":
                    self.show_device_state(a, b)
                elif kind == "progress":
                    done, total = a
                    if total:
                        self.progress.stop()
                        self.progress.configure(mode="determinate", maximum=total, value=done)
                    self.progressText.configure(text=b)
                elif kind == "done":
                    self.busy = False
                    self.progress.stop()
                    self.progress.configure(mode="determinate", maximum=1, value=1)
                    self.progressText.configure(text=("Preview: " if a else "Done: ") + b)
                    self.refresh_buttons()
                    self.refresh_watcher_status()
        except queue.Empty:
            pass
        self.root.after(100, self.drain_events)

    # ------------------------------------------------------------ misc

    def show_setup_help(self):
        messagebox.showinfo("Phone setup", SETUP_STEPS)

    def open_path(self, path):
        if os.path.exists(path):
            os.startfile(path)
        else:
            messagebox.showinfo("Phone Backup", f"{path} doesn't exist yet.")


if __name__ == "__main__":
    BackupApp()
