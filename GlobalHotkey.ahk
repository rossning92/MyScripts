#SingleInstance, Force
#InstallKeybdHook
#include ahk/ExplorerHelper.ahk
#include ahk/WaitKey.ahk

LastScriptName := ""
LastScriptStartTime := 0
MatchClipboard := {{MATCH_CLIPBOARD}}
OnClipboardChange("ClipChanged")
return

{{HOTKEYS}}

StartScript(scriptName, scriptPath)
{
    global LastScriptStartTime
    global LastScriptName

    UpdateExplorerInfo()
    now := A_TickCount
    if (scriptName = LastScriptName and now - LastScriptStartTime < 1000) {
        options := "--restart-instance true"
        Send {Alt Up}{Ctrl Up}{Shift Up} ; prevent wrong windows getting focus
    } else {
        options := "--restart-instance false"
    }
    Run "{{PYTHON_EXEC}}" "{{START_SCRIPT}}" %options% "%scriptPath%",, Hide

    LastScriptStartTime := now
    LastScriptName := scriptName
}

RunLastScript()
{
    Run "{{PYTHON_EXEC}}" --restart-instance true "{{START_SCRIPT}}",, Hide
}

ClipChanged(type) {
    global MatchClipboard

    if WinActive("ahk_exe vncviewer.exe") {
        return
    }

    if (type = 1) { ; clipboard has text
        text := Clipboard
        matchedScript := []
        matchedText := []
        message := ""

        ; Find all matched scripts
        for _index, item in MatchClipboard
        {
            regex := item[1]
            scriptName := item[2]
            if (RegExMatch(text, regex, match)) {
                message .= "[" (matchedScript.Length() + 1) "] " scriptName " | " match "`n"
                matchedScript.Push(item)
                matchedText.Push(match)
            }
        }

        if (matchedScript.Length() > 0) {
            key := WaitKey(message)
            if ( key <> "" and InStr("0123456789", key) ) {
                index := Ord(key) - Ord("0")
                scriptPath := matchedScript[index][3]
                match := matchedText[index]
                Run, "{{PYTHON_EXEC}}" "{{START_SCRIPT}}" "%scriptPath%" "%match%"
            }
        }
    }
}
