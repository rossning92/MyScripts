$ErrorActionPreference = "Stop"
Set-Service -Name sshd -Status running -StartupType automatic
Start-Service sshd