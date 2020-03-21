#SingleInstance, Force

is_recording := False

PROJECT_DIR = C:\Data\ep14
AUDIO_RECORDER_TITLE = r/audio/recorder

SetWorkingDir, %PROJECT_DIR%

WinClose, %AUDIO_RECORDER_TITLE%
Run, cmd /c title %AUDIO_RECORDER_TITLE% & set "PYTHONPATH=%A_ScriptDir%\..\..\..\..\libs" & set "RECORD_OUT_DIR=record" & python "%A_ScriptDir%\..\..\audio\recorder.py"

; Screencap (full screen)
$`::
    Send !{f9}
    
    if (not is_recording) {
        WinGet hwnd, ID, A
        Run, %LOCALAPPDATA%\carnac\Carnac.exe
        
        Run, cmd /c set "PYTHONPATH=%A_ScriptDir%\..\..\..\..\libs" & python "%A_ScriptDir%\_wait_for_screencap.py", , Min, pid_screencap
        
        Sleep 1000
        WinActivate ahk_id %hwnd%
    } else {
        Process, Close, Carnac.exe
        
        WinActivate, ahk_pid %pid_screencap%
    }
    
    is_recording := not is_recording
    
return

; Start recording
$F7::
    ControlSend, , r, %AUDIO_RECORDER_TITLE%
return

; Stop recording
$F8::
    ControlSend, , s, %AUDIO_RECORDER_TITLE%
    s := GetLatestRecoding()
    s = <!--- audio('record/%s%') -->
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
    Send ^s
    Run, cmd /c set "PYTHONPATH=%A_ScriptDir%\..\..\..;%A_ScriptDir%\..\..\..\..\libs" & python "%A_ScriptDir%\_export_final_audio.py" || pause
return

GetLatestRecoding()
{
    Loop record\*.wav
    if ( A_LoopFileTimeModified >= Time )
        Time := A_LoopFileTimeModified, File := A_LoopFileName
    
    return File
}