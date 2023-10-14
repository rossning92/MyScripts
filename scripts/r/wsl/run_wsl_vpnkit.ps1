# Workaround for WSL2 network broken on VPN:
# https://github.com/sakai135/wsl-vpnkit#setup-as-a-distro


$output = & wsl -l
if ( $output -contains 'wsl-vpnkit') {
    Write-Output "'wsl-vpnkit' distro already installed."
}
else {
    Set-Location "$env:USERPROFILE\Downloads"

    $downloadUrl = "https://github.com/sakai135/wsl-vpnkit/releases/download/v0.4.1/wsl-vpnkit.tar.gz"
    $outputFile = "wsl-vpnkit.tar.gz"
    Invoke-WebRequest -Uri $downloadUrl -OutFile $outputFile

    wsl --import wsl-vpnkit --version 2 $env:USERPROFILE\wsl-vpnkit wsl-vpnkit.tar.gz

    Remove-Item wsl-vpnkit.tar.gz
}

# Run wsl-vpnkit in the foreground.
wsl.exe -d wsl-vpnkit --cd /app wsl-vpnkit

# Uninstall
# wsl --unregister wsl-vpnkit