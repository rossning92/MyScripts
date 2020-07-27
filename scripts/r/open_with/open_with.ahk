#SingleInstance, Force
#InstallKeybdHook

#include ../../../libs/ahk/ExplorerHelper.ahk

SetWorkingDir %A_ScriptDir%

EnvSet, PYTHONPATH, %A_ScriptDir%\..\..\..\libs`;%A_ScriptDir%\..\..\..\scripts

#if WinActive("ahk_exe explorer.exe") or WinActive("ahk_exe everything.exe") or WinActive("ahk_exe Nomad.exe") or WinActive("ahk_exe FreeCommander.exe") or WinActive("ahk_exe doublecmd.exe")

    F3::
        WriteExplorerInfo(A_Temp "\ow_explorer_info.json")
        Run ..\..\..\bin\python36.cmd open_with_.py 0
        return

	F4::
		WriteExplorerInfo(A_Temp "\ow_explorer_info.json")
        Run ..\..\..\bin\python36.cmd open_with_.py 1
        return

#if


GetSelectedFilePath()
{
	; Save clipboard
    clipSaved := ClipboardAll

	; Get file path
	Clipboard =
    Send ^c
    ClipWait, 0.2
    if ErrorLevel
        return
    filePath = %clipboard%

	; Restore clipboard
    Clipboard := clipSaved
    clipSaved =

	; Check file existance
	if not FileExist(filePath)
		return

    ; Check if selected file is a shortcut
    SplitPath filePath, , , ext
    StringLower ext, ext
    if (ext = "lnk")
    {
        ; get target file path
        FileGetShortcut %filePath%, filePath
    }

    return filePath
}
