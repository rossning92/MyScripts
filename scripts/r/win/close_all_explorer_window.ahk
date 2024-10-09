; Close all explorer windows
WinGet, winList, List, ahk_class CabinetWClass
Loop, %winList%
{
    this_id := winList%A_Index%
    WinClose, ahk_id %this_id%
}

; Close "(Finished)" windows
WinGet, winList, List, (Finished)
Loop, %winList%
{
    this_id := winList%A_Index%
    WinClose, ahk_id %this_id%
}