$ErrorActionPreference = "Stop"

$Config = @"
# The default is to check both .ssh/authorized_keys and .ssh/authorized_keys2
# but this is overridden so installations will only check .ssh/authorized_keys
AuthorizedKeysFile .ssh/authorized_keys

# override default of no subsystems
Subsystem sftp sftp-server.exe

Match Group administrators
    AuthorizedKeysFile __PROGRAMDATA__/ssh/administrators_authorized_keys

PermitEmptyPasswords no
PermitRootLogin no
AllowUsers ross
GatewayPorts yes
"@

Set-Content "C:\ProgramData\ssh\sshd_config" $Config

Restart-Service -Name sshd
