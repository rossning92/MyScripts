#include ../../../ahk/Window.ahk

Menu, Tray, Icon, AnimationToolkit.ico
#SingleInstance, Force

SCRIPT_DIR := A_WorkingDir
VIDEO_PROJECT_DIR = {{VIDEO_PROJECT_DIR}}

ExtraArgs = --out_dir="%VIDEO_PROJECT_DIR%\screencap" --no_audio

SetWorkingDir, %VIDEO_PROJECT_DIR%

return

$F10::
    RunScript(SCRIPT_DIR . "\screenshot_.py")
return

$F6::
    SetTitleMatchMode, 2
    if (WinActive("ahk_exe chrome.exe")) {
        SetWindowPos("A", 0, 0, 1950, 1200)
        Sleep 500
        RunScript("/r/videoedit/uiautomate/record_screen.py", ExtraArgs " --rect 1 120 1920 1080")
    } else if (WinActive("ahk_class VMPlayerFrame")) {
        SetWindowPos("A", 0, 0, 1922, 1080 + 97)
        RunScript("/r/videoedit/uiautomate/record_screen.py", ExtraArgs " --rect 1 96 1920 1080")
    } else {
        GetWindowPos("A", x, y, w, h)
        RunScript("/r/videoedit/uiautomate/record_screen.py", ExtraArgs " --rect " x " " y " " w " " h)
    }
return

$^F6::
    RunScript("/r/videoedit/uiautomate/record_screen.py", ExtraArgs " --rect 0 0 1920 1080")
return

; Move vscode to the left side and browser to the right side of the screen.
; w := 1170
; SetWindowPos("ahk_exe Code.exe", 0, 0, w, 1080)
; SetWindowPos("ahk_exe chrome.exe", w, 0, 1920 - w, 1080)

RunScript(file, args="") {
    global SCRIPT_DIR
    global VIDEO_PROJECT_DIR

    commandLine = cmd /c set "VIDEO_PROJECT_DIR=%VIDEO_PROJECT_DIR%" && run_script "%file%" %args% || pause
    Run, %commandLine%, , , pid
return pid
}