$ErrorActionPreference = "Stop"
Set-Service -Name sshd -Status stopped -StartupType disabled
