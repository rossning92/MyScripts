$distros = wsl -l -q | ForEach-Object { $_.Trim().Replace("`0", "") } | Where-Object { $_ -ne "" }
if ($distros.Count -eq 0) {
    Write-Host "No WSL distributions found."
    exit
}

for ($i = 0; $i -lt $distros.Count; $i++) {
    Write-Host "$($i + 1). $($distros[$i])"
}

$choice = Read-Host "Select a distribution (1-$($distros.Count))"
if ($choice -match '^\d+$' -and $choice -ge 1 -and $choice -le $distros.Count) {
    $selectedDistro = $distros[$choice - 1]
    wsl --set-default $selectedDistro
    Write-Host "Set $selectedDistro as default."
} else {
    Write-Host "Invalid selection."
}
