#SingleInstance, Force
#InstallKeybdHook
#include ahk/ExplorerHelper.ahk

#If not WinActive("ahk_exe vncviewer.exe")

;!`::Run {{cmdline}} @console_title=%name%:new_window=auto:cd=1 || pause

{{hotkeys}}

; !q::HotkeySeq({ {{hotkey_seq_def}} })

#If

RunScript(name, path)
{
    UpdateExplorerInfo()
Run {{cmdline}} "%path%",, Hide
}

HotkeySeq(def) {
    matchlist := ""
    maxlen := 1
    for key, value in def {
        matchlist .= "," key
        if (maxlen < StrLen(key))
            maxlen := StrLen(key)
    }
    ToolTip, [Waiting Hotkey Sequence]
    Input command, % "L" maxlen, {Esc}, % SubStr(matchlist, 2)
    command := def[command]
    if command
        %command%()
    ToolTip
}

{{hotkey_def}}
