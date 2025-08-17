#SingleInstance, Force
#InstallKeybdHook

#include ../../../ahk/ExplorerHelper.ahk

SetWorkingDir %A_ScriptDir%

EnvSet, PYTHONPATH, %A_ScriptDir%\..\..\..\libs`;%A_ScriptDir%\..\..\..\scripts

#if WinActive("ahk_exe explorer.exe") or WinActive("ahk_exe everything.exe") or WinActive("ahk_exe Nomad.exe") or WinActive("ahk_exe FreeCommander.exe") or WinActive("ahk_exe doublecmd.exe")
    F3::
        UpdateExplorerInfo()
        Run run_script open_with.py --program-id 0 || pause
    return

    F4::
        UpdateExplorerInfo()
        Run run_script open_with.py --program-id 1 || pause
    return
#if