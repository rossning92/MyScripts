# Setup WSL2 on Windows host

# Enable mirrored networking mode (Windows 11 22H2+)
$wslConfig = "$env:USERPROFILE\.wslconfig"
if (!(Test-Path $wslConfig) -or !(Select-String -Path $wslConfig -Pattern 'networkingMode' -Quiet)) {
    Add-Content -Path $wslConfig -Value "[wsl2]`nnetworkingMode=mirrored"
}

# Auto-mount Google Drive (G:) on WSL login
wsl -u root -- mkdir -p /mnt/g
wsl -- bash -c 'grep -q "drvfs.*G:" ~/.profile 2>/dev/null || echo "
# Auto-mount Google Drive
if [ -d /mnt/g ] && ! mountpoint -q /mnt/g 2>/dev/null; then
    sudo mount -t drvfs G: /mnt/g 2>/dev/null
fi" >> ~/.profile'
wsl -u root -- bash -c 'echo "$(id -un 1000) ALL=(root) NOPASSWD: /usr/bin/mount -t drvfs G\: /mnt/g" > /etc/sudoers.d/gdrive-mount && chmod 440 /etc/sudoers.d/gdrive-mount'
wsl -- ln -sfn "/mnt/g/My Drive" ~/gdrive

wsl --shutdown
