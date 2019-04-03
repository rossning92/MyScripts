#SingleInstance, force
#Persistent
ToolTip, Keep awake...
SetTimer, NoSleep, 30000
Return

NoSleep:
    DllCall( "SetThreadExecutionState", UInt,0x80000003 )
    Return

$Esc::
    ExitApp