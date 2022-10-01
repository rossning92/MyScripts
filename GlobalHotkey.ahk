#SingleInstance, Force
#InstallKeybdHook
#include ahk/ExplorerHelper.ahk

#If not WinActive("ahk_exe vncviewer.exe")

;!`::Run {{cmdline}} @console_title=%name%:new_window=auto:cd=1 || pause

{{hotkeys}}

#If

RunScript(name, path)
{
    UpdateExplorerInfo()
Run {{cmdline}} "%path%",, Hide
}

{{hotkey_def}}
