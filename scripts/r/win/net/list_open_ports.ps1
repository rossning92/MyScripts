$nets = netstat -ano | select-string LISTENING
foreach ($n in $nets) {
    # make split easier PLUS make it a string instead of a match object:
    $p = $n -replace ' +', ' '
    # make it an array:
    $nar = $p.Split(' ')
    # pick last item:
    $pname = $(Get-Process -id $nar[-1]).ProcessName
    $ppath = $(Get-Process -id $nar[-1]).Path
    # print the modified line with processname instead of PID:
    $n -replace "$($nar[-1])", "$($nar[-1]) $($ppath) $($ppid) $($pname)"
}
