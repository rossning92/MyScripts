#include ../../../ahk/Window.ahk

Menu, Tray, Icon, animation_toolkit.ico
#SingleInstance, Force

SCRIPT_DIR := A_WorkingDir
VIDEO_PROJECT_DIR = {{VIDEO_PROJECT_DIR}}

is_recording := False

SetWorkingDir, %VIDEO_PROJECT_DIR%

return

$F10::
    RunScript(SCRIPT_DIR . "\screenshot_.py")
return

$F6::
    SetTitleMatchMode, 2
    if (WinActive("ahk_exe chrome.exe")) {
        SetWindowPos("A", 0, 0, 1950, 1250)
        Sleep 500
        RunScript("/r/videoedit/record_screen.py", "--rect 1 120 1920 1080")
    } else if (WinActive("ahk_exe WindowsTerminal.exe")) {
        ; SetWindowPos("A", 0, 0, 1440, 810)
        ; sleep 500
        ; RunScript("/r/videoedit/record_screen.py", "--rect 0 0 1440 810")
        RunScript("/r/videoedit/record_screen.py", "--rect 0 0 1920 1080")
    } else if (WinActive("ahk_class CabinetWClass")) {
        SetWindowPos("A", 0, 0, 1440, 810)
        RunScript("/r/videoedit/record_screen.py", "--rect 0 0 1440 810")
    } else {
        RunScript("/r/videoedit/record_screen.py", "--rect 0 0 1920 1080")
    }
return

$^F6::
    w := 1170
    SetWindowPos("ahk_exe Code.exe", 0, 0, w, 1080)
    SetWindowPos("ahk_exe chrome.exe", w, 0, 1920 - w, 1080)
return

RunScript(file, args="") {
    global SCRIPT_DIR
    global VIDEO_PROJECT_DIR

    commandLine = cmd /c set "VIDEO_PROJECT_DIR=%VIDEO_PROJECT_DIR%" && run_script "%file%" %args% || pause
    Run, %commandLine%, , , pid
return pid
}