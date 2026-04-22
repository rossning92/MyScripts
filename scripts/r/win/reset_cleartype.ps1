$ErrorActionPreference = "Stop"

# Reset ClearType desktop settings to Windows defaults
Set-ItemProperty "HKCU:\Control Panel\Desktop" -Name FontSmoothing -Value "2"
# 1 = grayscale AA (sub-pixel layout agnostic), 2 = ClearType sub-pixel AA
Set-ItemProperty "HKCU:\Control Panel\Desktop" -Name FontSmoothingType -Value 1
Set-ItemProperty "HKCU:\Control Panel\Desktop" -Name FontSmoothingGamma -Value 0x4B0
Set-ItemProperty "HKCU:\Control Panel\Desktop" -Name FontSmoothingOrientation -Value 1

# Reset WPF/Avalon ClearType tuning
Remove-Item "HKCU:\SOFTWARE\Microsoft\Avalon.Graphics\DISPLAY1" -ErrorAction SilentlyContinue

Write-Host "Font smoothing set to grayscale AA."
Write-Host "Log off and back on for changes to take full effect."
