$ErrorActionPreference = "Stop"

# https://github.com/frgnca/AudioDeviceCmdlets
Import-Module "$PSScriptRoot\AudioDeviceCmdlets.dll"
$audio_device = (Get-AudioDevice -List | Where-Object { $_.Name -like '*MIC_TEST*' -and $_.Type -eq 'Recording' }).ID
if (!$audio_device) { 
    Write-Host "ERROR: cannot find microphone." 
    Exit 1
}

Set-AudioDevice $audio_device | Out-Null
Set-AudioDevice -RecordingVolume 80
