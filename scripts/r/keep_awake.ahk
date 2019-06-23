#SingleInstance, force
#Persistent

CoordMode, ToolTip, Screen
ToolTip, Keep Awake`n(Alt-Esc to Exit), 0, 0
SetTimer, NoSleep, 30000
Return

NoSleep:
    DllCall( "SetThreadExecutionState", UInt,0x80000003 )
    Return

$!Esc::
    ExitApp