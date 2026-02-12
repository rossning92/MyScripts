#SingleInstance, Force
#InstallKeybdHook
#include ahk/ExplorerHelper.ahk
#include ahk/WaitKey.ahk

Menu, Tray, Icon, Shell32.dll, 42 ; Tree icon

LastScript := ""
MatchClipboard := {{MATCH_CLIPBOARD}}
OnClipboardChange("ClipChanged")
return

{{HOTKEYS}}

#enter::RestartLastScript()

StartScript(scriptName, scriptPath, restartInstance)
{
    global LastScript

    if WinExist(scriptName) and not restartInstance
    {
        WinActivate, %scriptName%
        return
    }

    UpdateExplorerInfo()
    now := A_TickCount
    options := ""
    Run "{{PYTHON_EXEC}}" "{{START_SCRIPT}}" --restart-instance %restartInstance% "%scriptPath%",, Hide

    LastScript := scriptPath
}

RestartLastScript()
{
    global LastScript
    if (LastScript <> "") {
        Run "{{PYTHON_EXEC}}" "{{START_SCRIPT}}" --restart-instance true %LastScript%,, Hide
    }
}

ClipChanged(type) {
    global MatchClipboard

    ; Early return if control key is not pressed down.
    Sleep 500
    if !GetKeyState("Control") {
        return
    }

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
