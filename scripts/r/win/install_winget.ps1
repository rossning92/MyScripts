# https://github.com/microsoft/winget-cli

# Get latest download url
Write-Host "Getting latest download URL..."
$URL = "https://api.github.com/repos/microsoft/winget-cli/releases/latest"
$URL = (Invoke-WebRequest -UseBasicParsing -Uri $URL).Content | ConvertFrom-Json |
Select-Object -ExpandProperty "assets" |
Where-Object "browser_download_url" -Match '.msixbundle' |
Select-Object -ExpandProperty "browser_download_url"

Write-Host "Downloading..."
$ProgressPreference = 'SilentlyContinue'
Invoke-WebRequest -Uri $URL -OutFile "Setup.msix" -UseBasicParsing

Write-Host "Installing..."
Add-AppxPackage -Path "Setup.msix"

Write-Host "Deleting setup file..."
Remove-Item "Setup.msix"
