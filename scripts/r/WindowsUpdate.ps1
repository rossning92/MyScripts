Clear-Host

Write-Host "0 -> Change setting in Windows Update app (default)"
Write-Host "1 -> Never check for updates (not recommended)"
Write-Host "2 -> Notify for download and notify for install"
Write-Host "3 -> Auto download and notify for install"
Write-Host "4 -> Auto download and schedule the install"

Write-Host "Enter any character to exit"
Write-Host
switch(Read-Host "Choose Window Update Settings"){
       0 {$UpdateValue = 0}
       1 {$UpdateValue = 1}
       2 {$UpdateValue = 2}
       3 {$UpdateValue = 3}
       4 {$UpdateValue = 4}
       Default{Exit}
}

$WindowsUpdatePath = "HKLM:SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\"
$AutoUpdatePath = "HKLM:SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU"

If(Test-Path -Path $WindowsUpdatePath) {
    Remove-Item -Path $WindowsUpdatePath -Recurse
}


If ($UpdateValue -gt 0) {
    New-Item -Path $WindowsUpdatePath
    New-Item -Path $AutoUpdatePath
}

If ($UpdateValue -eq 1) {
    Set-ItemProperty -Path $AutoUpdatePath -Name NoAutoUpdate -Value 1
}

If ($UpdateValue -eq 2) {
    Set-ItemProperty -Path $AutoUpdatePath -Name NoAutoUpdate -Value 0
    Set-ItemProperty -Path $AutoUpdatePath -Name AUOptions -Value 2
    Set-ItemProperty -Path $AutoUpdatePath -Name ScheduledInstallDay -Value 0
    Set-ItemProperty -Path $AutoUpdatePath -Name ScheduledInstallTime -Value 3
}

If ($UpdateValue -eq 3) {
    Set-ItemProperty -Path $AutoUpdatePath -Name NoAutoUpdate -Value 0
    Set-ItemProperty -Path $AutoUpdatePath -Name AUOptions -Value 3
    Set-ItemProperty -Path $AutoUpdatePath -Name ScheduledInstallDay -Value 0
    Set-ItemProperty -Path $AutoUpdatePath -Name ScheduledInstallTime -Value 3
}

If ($UpdateValue -eq 4) {
    Set-ItemProperty -Path $AutoUpdatePath -Name NoAutoUpdate -Value 0
    Set-ItemProperty -Path $AutoUpdatePath -Name AUOptions -Value 4
    Set-ItemProperty -Path $AutoUpdatePath -Name ScheduledInstallDay -Value 0
    Set-ItemProperty -Path $AutoUpdatePath -Name ScheduledInstallTime -Value 3
}