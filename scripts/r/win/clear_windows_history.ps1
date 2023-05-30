# Delete recent items contents
Remove-Item HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\RunMRU\    -Verbose -Force -ErrorAction SilentlyContinue
Remove-Item HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\TypedPaths -Verbose -Force -ErrorAction SilentlyContinue

# Delete powershell history
Remove-Item (Get-PSReadlineOption).HistorySavePath
