#SingleInstance, Force
#include %A_ScriptDir%\..\..\..\ahk\Window.ahk

#v::
    if not WinExist("ahk_exe code.exe") {
        EnvGet, LocalAppData, LocalAppData
        Run run_script r/vscode/run_vscode.py
    } else {
        ActivateWindowByTitle("ahk_exe code.exe")
    }
return
