WinActivate FL Studio 12
Send {Space}

Run python -c "from _script import *; run_script('camera_record.py')"
return

$Space::
    WinActivate FL Studio 12
    Send {Space}

    WinActivate camera_record
    Send {Enter}
    ExitApp
    return