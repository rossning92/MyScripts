$files = $args
foreach ($file in $files) {
    Get-FileHash $file
}