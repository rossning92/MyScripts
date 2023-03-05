# https://learn.microsoft.com/en-us/windows/wsl/networking
$ErrorActionPreference = "Stop"

netsh interface portproxy reset

$TargetIp = $(wsl hostname -I)
$TargetIp = "127.0.0.1"
Write-Output $TargetIp

$ConnectPort = "$Env:_PORT_NUMBER"
$ListenPort = "$ConnectPort"

netsh interface portproxy set v4tov4 listenport="$ListenPort" listenaddress=0.0.0.0 connectport=$ConnectPort connectaddress=$TargetIp protocol=tcp

# Open port in firewall
netsh advfirewall firewall add rule name="Allowing LAN connections" dir=in action=allow protocol=TCP localport=$ListenPort

netsh interface portproxy show all

Write-Output "Check if port $ListenPort is open:"
netstat -an | findstr ":$ListenPort "
