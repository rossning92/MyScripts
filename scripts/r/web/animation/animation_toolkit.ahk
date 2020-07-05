Menu, Tray, Icon, animation_toolkit.ico
#SingleInstance, Force

SCRIPT_DIR := A_WorkingDir

is_recording := False

VIDEO_PROJECT_DIR = {{VIDEO_PROJECT_DIR}}
AUDIO_RECORDER_TITLE = r/audio/recorder

SetWorkingDir, %VIDEO_PROJECT_DIR%

return

$F10::
    RunScript("_screenshot.py", True)
return

; Screencap (full screen)
$^F6::
    ToggleRecording()
return

$F6::
    ToggleRecording(False)
return

!Esc::
    WinClose, %AUDIO_RECORDER_TITLE%
    ExitApp
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
        
        RunScript(SCRIPT_DIR . "\_wait_for_screencap.py")
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
    
    Run, cmd /c set "VIDEO_PROJECT_DIR=%VIDEO_PROJECT_DIR%" && %SCRIPT_DIR%\..\..\..\..\bin\run_script.exe "%file%" || pause, , %minParam%, pid
    return pid
}