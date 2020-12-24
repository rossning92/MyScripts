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

; Screencap (full screen)
$^F6::
    ToggleRecording()
return

$F6::
    if (WinActive("ahk_exe chrome.exe")) {
        SetWindowPos("A", 0, 0, 2300, 1400)
        Sleep 500
        RunScript("/r/web/animation/record_screen.py", "--rect 0 64 2272 1278")
    } else if (WinActive("ahk_exe Code.exe")) {
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

ToggleRecording(enable_carnac:=True)
{
    global SCRIPT_DIR
    global is_recording
    global pid_screencap

    if (not is_recording) {
        Send !{f9}

        WinGet hwnd, ID, A

        if (enable_carnac) {
            Run, %LOCALAPPDATA%\carnac\Carnac.exe
        }

        Sleep 1000
        WinActivate ahk_id %hwnd%
    } else {
        if (enable_carnac) {
            Process, Close, Carnac.exe
        }

        Send !{f9}
        Sleep, 1000 ; Make sure that the window is not pop up when recording stops.

        RunScript(SCRIPT_DIR . "\save_screencap_.py")
    }

    is_recording := not is_recording
}

RunScript(file, args="") {
    global SCRIPT_DIR
    global VIDEO_PROJECT_DIR

    commandLine := "cmd /c set ""VIDEO_PROJECT_DIR=" VIDEO_PROJECT_DIR """"
    commandLine .= " && " SCRIPT_DIR "\..\..\..\..\bin\run_script.exe """ file """ -- " args
    commandLine .= " || pause"

    Run, %commandLine%, , , pid
return pid
}