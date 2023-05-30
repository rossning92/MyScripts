#SingleInstance, Force
#InstallKeybdHook
#include ahk/ExplorerHelper.ahk

LastScriptName := ""
LastScriptStartTime := 0
MatchClipboard := {{MATCH_CLIPBOARD}}
OnClipboardChange("ClipChanged")
return

#If not WinActive("ahk_exe vncviewer.exe")

^!r::RunLastScript()
{{HOTKEYS}}

#If

RunScript(scriptName, scriptPath)
{
    global LastScriptStartTime
    global LastScriptName

    UpdateExplorerInfo()
    now := A_TickCount
    if (scriptName = LastScriptName and now - LastScriptStartTime < 1000) {
        EnvSet, RESTART_INSTANCE, 1
        Send {Alt Up}{Ctrl Up}{Shift Up} ; prevent wrong windows getting focus
    } else {
        EnvSet, RESTART_INSTANCE, 0
    }
    Run "{{PYTHON_EXEC}}" "{{START_SCRIPT}}" "%scriptPath%",, Hide

    LastScriptStartTime := now
    LastScriptName := scriptName
}

RunLastScript()
{
    EnvSet, RESTART_INSTANCE, 1
    Run "{{PYTHON_EXEC}}" "{{START_SCRIPT}}",, Hide
}

WaitKey(prompt) {
    CoordMode, ToolTip, Screen
    xpos := A_ScreenWidth // 2
    ypos := A_ScreenHeight // 2
    ToolTip, %prompt%, %xpos%, %ypos%
    Input, key, L1T10, {LButton}{RButton}{MButton}{LControl}{RControl}{LAlt}{RAlt}{LShift}{RShift}{LWin}{RWin}{AppsKey}{F1}{F2}{F3}{F4}{F5}{F6}{F7}{F8}{F9}{F10}{F11}{F12}{Left}{Right}{Up}{Down}{Home}{End}{PgUp}{PgDn}{Del}{Ins}{BS}{CapsLock}{NumLock}{PrintScreen}{Pause}
    ToolTip
    return key
}

ClipChanged(type) {
    global MatchClipboard

    if (type = 1) { ; clipboard has text
        text := Clipboard
        matchedScript := []
        message := ""

        ; Find all matched scripts
        for _index, item in MatchClipboard
        {
            regex := item[1]
            scriptName := item[2]
            if (RegExMatch(text, regex)) {
                message .= "[" (matchedScript.Length() + 1) "] " scriptName "`n"
                matchedScript.Push(item)
            }
        }

        if (matchedScript.Length() > 0) {
            key := WaitKey(message)
            if ( key <> "" and InStr("0123456789", key) ) {
                index := Ord(key) - Ord("0")
                scriptPath := matchedScript[index][3]
                Run, "{{PYTHON_EXEC}}" "{{RUN_SCRIPT}}" "%scriptPath%" "%text%"
            }
        }
    }
}
