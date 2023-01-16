$ErrorActionPreference = "Stop"
$Env:WSL_UTF8 = 1

$Distro = "Ubuntu-20.04"

$out = $(wsl --list)
if ($out -like "*$Distro*") {
    $confirmation = Read-Host "$Distro already installed. Uninstall first? (y/n)"
    if ($confirmation -eq 'y') {
        wsl --unregister "$Distro"
    }
}

wsl --install --distribution "$Distro"
wsl --set-default "$Distro"
