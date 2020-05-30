Menu, Tray, Icon, animation_toolkit.ico
#SingleInstance, Force

SCRIPT_DIR := A_WorkingDir

is_recording := False

PROJECT_DIR = {{VIDEO_PROJECT_DIR}}
AUDIO_RECORDER_TITLE = r/audio/recorder

SetWorkingDir, %PROJECT_DIR%

return

$F10::
    RunPython("_screenshot.py", True)
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
        
        Run, cmd /c set "PYTHONPATH=%SCRIPT_DIR%\..\..\..\..\libs" & python "%SCRIPT_DIR%\_wait_for_screencap.py", , Min, pid_screencap
        
        Sleep 1000
        WinActivate ahk_id %hwnd%
    } else {
        if (enable_carnac) {
            Process, Close, Carnac.exe
        }
        
        Send !{f9}
        Sleep, 1000 ; Make sure that the window is not pop up when recording stops.
        
        WinActivate, ahk_pid %pid_screencap%
    }
    
    is_recording := not is_recording
}

RunPython(file, min:=False) {
    global SCRIPT_DIR
    
    if (min) {
        minParam = Min
    } else {
        minParam =
    }
    
    Run, cmd /c set "PYTHONPATH=%SCRIPT_DIR%\..\..\..;%SCRIPT_DIR%\..\..\..\..\libs" & python "%SCRIPT_DIR%\%file%" || pause, , %minParam%
}