#include ../../../../libs/ahk/Window.ahk

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
    if (WinActive("- movy")) {
        SetWindowPos("ahk_exe Code.exe", 0, 0, 960, 1080)
        SetWindowPos("ahk_exe chrome.exe", 960, 0, 960, 1080)
        sleep 500
        RunScript("/r/web/animation/record_screen.py", "--rect 0 0 1920 1080")
    } else if (WinActive("ahk_exe chrome.exe")) {
        SetWindowPos("A", 0, 0, 1950, 1250)
        Sleep 500
        RunScript("/r/web/animation/record_screen.py", "--rect 1 120 1920 1080")
    } else if (WinActive("ahk_exe Code.exe") or WinActive("ahk_exe texworks.exe") or WinActive("OverlayWindow")) {
        SetWindowPos("A", 0, 0, 1920, 1080)
        sleep 500
        RunScript("/r/web/animation/record_screen.py", "--rect 0 0 1920 1080")
    } else if (WinActive("ahk_exe WindowsTerminal.exe") or WinActive("ahk_class CabinetWClass")) {
        SetWindowPos("A", 0, 0, 1440, 810)
        sleep 500
        RunScript("/r/web/animation/record_screen.py", "--rect 0 0 1440 810")
    } else {
        RunScript("/r/web/animation/record_screen.py")
    }

return

RunScript(file, args="") {
    global SCRIPT_DIR
    global VIDEO_PROJECT_DIR

    commandLine := "cmd /c set ""VIDEO_PROJECT_DIR=" VIDEO_PROJECT_DIR """"
    commandLine .= " && " SCRIPT_DIR "\..\..\..\..\bin\run_script.exe """ file """ -- " args
    commandLine .= " || pause"

    Run, %commandLine%, , , pid
return pid
}