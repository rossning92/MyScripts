# https://learn.microsoft.com/en-us/windows/wsl/networking
$ErrorActionPreference = "Stop"

netsh interface portproxy reset

$TargetIp = $(wsl hostname -I)
Write-Output $TargetIp

$PortNumber = "$Env:_PORT_NUMBER"

netsh interface portproxy set v4tov4 listenport="$PortNumber" listenaddress=0.0.0.0 connectport=$PortNumber connectaddress=$TargetIp protocol=tcp

# Open port in firewall
netsh advfirewall firewall add rule name="Allowing LAN connections" dir=in action=allow protocol=TCP localport=$PortNumber

netsh interface portproxy show all
netstat -ano | findstr :$PortNumber
