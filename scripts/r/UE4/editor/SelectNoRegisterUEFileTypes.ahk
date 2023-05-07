#SingleInstance, Force

loop {
    if (WinExist("File Types", "Register Unreal Engine file types"))
    {
        ControlSend, ahk_parent, !n, File Types, Register Unreal Engine file types ; send Alt + N to last found window
    }
    Sleep, 1000
}
