Menu, Tray, Icon, animation_toolkit.ico
#SingleInstance, Force

SCRIPT_DIR := A_WorkingDir

is_recording := False

PROJECT_DIR = {{VIDEO_PROJECT_DIR}}
AUDIO_RECORDER_TITLE = r/audio/recorder

SetWorkingDir, %PROJECT_DIR%

WinClose, %AUDIO_RECORDER_TITLE%
Run, cmd /c title %AUDIO_RECORDER_TITLE% & set "PYTHONPATH=%SCRIPT_DIR%\..\..\..\..\libs" & set "RECORD_OUT_DIR=record" & python "%SCRIPT_DIR%\..\..\audio\recorder.py"

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

; Start recording
$F7::
    ControlSend, , r, %AUDIO_RECORDER_TITLE%
return

; Stop recording
$F8::
    ControlSend, , s, %AUDIO_RECORDER_TITLE%
    s := GetLatestRecoding()
    s = record('%s%')
    Clipboard := s
    if WinActive("ahk_exe code.exe") {
        Send ^v
    }
return

; Noise
$F9::
    ControlSend, , n, %AUDIO_RECORDER_TITLE%
return

; Export
$F12::
    RunPython("_export_final_audio.py")
return

!Esc::
    WinClose, %AUDIO_RECORDER_TITLE%
    ExitApp
return

GetLatestRecoding()
{
    Loop record\*.wav
    if ( A_LoopFileTimeModified >= Time ) {    
        Time := A_LoopFileTimeModified, File := A_LoopFileName
    }
    
return File
}

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
        Sleep, 1000  ; Make sure that the window is not pop up when recording stops.
        
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