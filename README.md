# phoneBackupOrganiser
Streamlining the local organisation of photos, videos, & files imported from your phone.

This python script moves and organises the mess of files from any folder, into an organised directory sorted by years and months

![image](https://user-images.githubusercontent.com/95185431/213944376-4ebe2676-a757-4e55-944f-fd3b747063a0.png)

## Automatic backup (plug in and forget)

`phone_backup.py` runs in the background and, whenever your phone is plugged in, copies any new photos & videos
straight into `D:\Phone Media Backups\YYYY\YYYY-MM`. Files on the phone are never deleted, and a small database
(`.phone_backup.db` in the backup folder) remembers what has already been copied so each plug-in only grabs what's new.

### One-time phone setup
1. **Settings → About phone** → tap **Build number** 7 times to unlock Developer options.
2. **Settings → System → Developer options** → turn on **USB debugging**.
3. Plug the phone in, unlock it, and tap **Allow** (tick *Always allow from this computer*).

### Control panel
Open **Phone Backup** from the Desktop or Start menu (create those shortcuts once with
`powershell -ExecutionPolicy Bypass -File install_startup.ps1 -Shortcuts`). In the window you can:
- see whether your phone is connected (and get setup help if it isn't),
- choose the backup folder and folder layout,
- tick which phone folders to include (Camera, Screenshots, WhatsApp, ...),
- turn **automatic backup** on/off (runs silently in the background from login),
- **Preview** what's new, or **Back up now** with a progress bar and Cancel button.

Settings are saved to `config.json` automatically.

### Command line (optional)
```
python phone_backup.py --dry-run   # show what would be copied
python phone_backup.py --once      # back up now
```
Logs are in `logs/phone_backup.log`.

## Manual organiser (original GUI)

How to:
1. Locate the directory from which you wish to organise.
2. Select the directory you would like the organised files to be moved to.
3. Input the desired year & month ranges to organise.
4. Press sort

