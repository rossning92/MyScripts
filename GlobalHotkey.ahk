#SingleInstance, Force
#include ahk/ExplorerHelper.ahk

RunScript(name, path)
{
    if WinExist(name)
    {
        WinActivate % name
    }
    else if WinExist("Administrator: " name)
    {
        WinActivate % "Administrator: " name
    }
    else
    {
        UpdateExplorerInfo()
        Run {{run_script}} @console_title=%name%:restart_instance=0:new_window=auto "%path%" || pause
    }
}

#If not WinActive("ahk_exe vncviewer.exe")

f12::Run {{run_script}} @console_title=%name%:new_window=auto || pause
{{htk_definitions}}

#If
