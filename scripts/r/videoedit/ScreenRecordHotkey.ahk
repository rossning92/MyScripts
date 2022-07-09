#SingleInstance, Force
#include %A_ScriptDir%\..\..\..\ahk\Window.ahk

; SCREEN_RECORD_DIR
Menu, Tray, Icon, ScreenRecordHotkey.ico
SetTitleMatchMode, 2

$F6::
    RunScript("r/videoedit/uiautomate/record_screen.py", "--no_audio --rect 0 0 1920 1080")
return

$^F6::
    if (WinActive("ahk_exe chrome.exe")) {
        SetWindowPos("A", 0, 0, 1950, 1200)
        Sleep 500
        RunScript("r/videoedit/uiautomate/record_screen.py", "--no_audio --rect 1 120 1920 1080")
    } else if (WinActive("ahk_class VMPlayerFrame")) {
        SetWindowPos("A", 0, 0, 1922, 1080 + 97)
        RunScript("r/videoedit/uiautomate/record_screen.py", "--no_audio --rect 1 96 1920 1080")
    } else {
        GetWindowPos("A", x, y, w, h)
        RunScript("r/videoedit/uiautomate/record_screen.py", "--no_audio --rect " x " " y " " w " " h)
    }
return

RunScript(file, args="") {
    commandLine = cmd /c run_script "%file%" %args% || pause
    Run, %commandLine%
}