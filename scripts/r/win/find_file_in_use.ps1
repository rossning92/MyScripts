# https://superuser.com/questions/117902/find-out-which-process-is-locking-a-file-or-folder-in-windows

$FileOrFolderPath = $args[0]

# openfiles /local on

if ((Test-Path -Path $FileOrFolderPath) -eq $false) {
    Write-Warning "File or directory does not exist."
}
else {
    $LockingProcess = CMD /C "openfiles /query /fo table | find /I ""$FileOrFolderPath"""
    Write-Host $LockingProcess
}