#SingleInstance, Force
#InstallKeybdHook
#include ahk/ExplorerHelper.ahk

LastScriptName := ""
LastScriptStartTime := 0

#If not WinActive("ahk_exe vncviewer.exe")

^#r::RunLastScript()
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
    EnvSet, RESTART_INSTANCE, 0
    Run "{{PYTHON_EXEC}}" "{{START_SCRIPT}}",, Hide
}
