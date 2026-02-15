#SingleInstance, force
#Persistent

Menu, Tray, Icon, Shell32.dll, 28 ; Power icon
CoordMode, ToolTip, Screen
SetTimer, NoSleep, 30000
Return

NoSleep:
    DllCall( "SetThreadExecutionState", UInt,0x80000003 )
Return

$!Esc::
ExitApp
