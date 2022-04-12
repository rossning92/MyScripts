#SingleInstance, Force
#include ahk/ExplorerHelper.ahk

#If not WinActive("ahk_exe vncviewer.exe")

;!`::Run {{run_script}} @console_title=%name%:new_window=auto:cd=1 || pause

{{hotkeys}}

; !q::HotkeySeq({ {{hotkey_seq_def}} })

#If

RunScript(name, path)
{
    if WinExist(name)
    {
        WinActivate % name
    }
    else if WinExist("Administrator:  " name)
    {
        WinActivate % "Administrator:  " name
    }
    else
    {
        UpdateExplorerInfo()
        Run {{run_script}} @console_title=%name%:restart_instance=0:new_window=auto:cd=1 "%path%" || pause
    }
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
