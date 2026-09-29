# Adds (or with -Uninstall, removes) a Startup-folder shortcut that runs the
# phone backup watcher silently every time you log in.
# With -Shortcuts, instead adds "Phone Backup" to the Desktop and Start menu to open the window.
param([switch]$Uninstall, [switch]$Shortcuts)

if ($Shortcuts) {
    $pythonw = Join-Path (Split-Path (Get-Command python -ErrorAction Stop).Source) 'pythonw.exe'
    $gui = Join-Path $PSScriptRoot 'phone_backup_gui.pyw'
    $shell = New-Object -ComObject WScript.Shell
    foreach ($folder in [Environment]::GetFolderPath('Desktop'), [Environment]::GetFolderPath('Programs')) {
        $link = $shell.CreateShortcut((Join-Path $folder 'Phone Backup.lnk'))
        $link.TargetPath = $pythonw
        $link.Arguments = "`"$gui`""
        $link.WorkingDirectory = $PSScriptRoot
        $link.IconLocation = "$env:SystemRoot\System32\imageres.dll,-1023"
        $link.Description = 'Back up photos & videos from your phone'
        $link.Save()
        Write-Host "Created $(Join-Path $folder 'Phone Backup.lnk')"
    }
    return
}

$shortcutPath = Join-Path ([Environment]::GetFolderPath('Startup')) 'Phone Backup Watcher.lnk'
$script = Join-Path $PSScriptRoot 'phone_backup.py'

if ($Uninstall) {
    Get-CimInstance Win32_Process -Filter "Name = 'pythonw.exe'" |
        Where-Object CommandLine -like '*phone_backup.py*--watch*' |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Confirm:$false }
    Remove-Item $shortcutPath -ErrorAction SilentlyContinue
    Write-Host 'Phone backup watcher removed from Startup and stopped.'
    return
}

$python = (Get-Command python -ErrorAction Stop).Source
$pythonw = Join-Path (Split-Path $python) 'pythonw.exe'
if (-not (Test-Path $pythonw)) { throw "pythonw.exe not found next to $python" }

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $pythonw
$shortcut.Arguments = "`"$script`" --watch"
$shortcut.WorkingDirectory = $PSScriptRoot
$shortcut.Description = 'Backs up phone photos & videos when plugged in'
$shortcut.Save()

# Start it now too, so there's no need to log out and back in
Start-Process $pythonw -ArgumentList "`"$script`" --watch" -WorkingDirectory $PSScriptRoot
Write-Host "Installed: $shortcutPath"
Write-Host 'Watcher is running. Plug in your phone to back it up.'
