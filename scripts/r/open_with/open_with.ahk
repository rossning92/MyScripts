#SingleInstance, Force
#InstallKeybdHook

#include ../../../libs/ahk/ExplorerHelper.ahk

SetWorkingDir %A_ScriptDir%

EnvSet, PYTHONPATH, %A_ScriptDir%\..\..\..\libs`;%A_ScriptDir%\..\..\..\scripts

#if WinActive("ahk_exe explorer.exe") or WinActive("ahk_exe everything.exe") or WinActive("ahk_exe Nomad.exe") or WinActive("ahk_exe FreeCommander.exe") or WinActive("ahk_exe doublecmd.exe")
    
F3::
    UpdateExplorerInfo()
    Run ..\..\..\bin\python36.cmd open_with_.py 0
return

F4::
    UpdateExplorerInfo()
    Run ..\..\..\bin\python36.cmd open_with_.py 1
return

#if