Menu, Tray, Icon, animation_toolkit.ico
#SingleInstance, Force

SCRIPT_DIR := A_WorkingDir
VIDEO_PROJECT_DIR = {{VIDEO_PROJECT_DIR}}

is_recording := False

SetWorkingDir, %VIDEO_PROJECT_DIR%

return

$F10::
    RunScript(SCRIPT_DIR . "\screenshot_.py", min:=True)
return

; Screencap (full screen)
$^F6::
    ToggleRecording()
return

$F6::
    RunScript(SCRIPT_DIR . "\record_screen.py")
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

RunScript(file, min:=False) {
    global SCRIPT_DIR
    global VIDEO_PROJECT_DIR

    if (min) {
        minParam = Min
    } else {
        minParam =
    }

    args := "cmd /c set ""VIDEO_PROJECT_DIR=" VIDEO_PROJECT_DIR """"
    args .= " && " SCRIPT_DIR "\..\..\..\..\bin\run_script.exe """ file """"
    args .= " || pause"

    Run, %args%, , %minParam%, pid
return pid
}