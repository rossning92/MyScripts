# https://learn.microsoft.com/en-us/windows/wsl/networking
$ErrorActionPreference = "Stop"

netsh interface portproxy reset

# $ConnectIp = $(wsl hostname -I)
$ListenIp = "0.0.0.0"
$ConnectIp = "127.0.0.1"

Write-Output $ConnectIp

function Set-PortProxy {
    param(
        [string]$ConnectIp,
        [string]$ConnectPort,
        [string]$ListenIp,
        [string]$ListenPort
    )
    Write-Host "Setting up port proxy for ${ConnectIp}:${ConnectPort} => ${ListenIp}:${ListenPort}"

    netsh interface portproxy set v4tov4 listenport="$ListenPort" listenaddress=$ListenIp connectport=$ConnectPort connectaddress=$ConnectIp protocol=tcp

    # Open port in firewall
    netsh advfirewall firewall add rule name="Allowing LAN connections from port $ListenPort" dir=in action=allow protocol=TCP localport=$ListenPort
}

foreach ($ConnectPort in $Env:_PORT_NUMBERS.Split(' ')) {
    $ListenPort = "$ConnectPort"
    Set-PortProxy -ConnectIp $ConnectIp -ConnectPort $ConnectPort -ListenIp $ListenIp -ListenPort $ConnectPort
}

# Sanity check
netsh interface portproxy show all

# Write-Output "Check if port $ListenPort is open:"
# netstat -an | findstr ":$ListenPort "
