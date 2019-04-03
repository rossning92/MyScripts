#SingleInstance, force
#Persistent
ToolTip, Keep Awake`n(Alt-Esc to Exit)
SetTimer, NoSleep, 30000
Return

NoSleep:
    DllCall( "SetThreadExecutionState", UInt,0x80000003 )
    Return

$!Esc::
    ExitApp