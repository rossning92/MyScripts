#SingleInstance, Force
SetWorkingDir %A_ScriptDir%

loop {
    if (WinExist("File Types", "Register Unreal Engine file types"))
    {
        ControlSend, ahk_parent, `n, File Types, Register Unreal Engine file types ; press enter key
        ExitApp
    }
    Sleep, 1000
}
