$ErrorActionPreference = "Stop"

$Config = @"
PubkeyAuthentication yes

# override default of no subsystems
Subsystem sftp sftp-server.exe

PermitEmptyPasswords no
PermitRootLogin no
AllowUsers ross
GatewayPorts yes
"@

Set-Content "C:\ProgramData\ssh\sshd_config" $Config

Restart-Service -Name sshd
