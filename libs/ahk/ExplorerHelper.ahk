#include %A_LineFile%\..\JSON.ahk 

WriteExplorerInfo(file)
{
    data := { "current_folder" : Explorer_GetPath(), "selected_files" : Explorer_GetSelected() }
    str := JSON.Dump(data, "", 4)
    FileDelete, %file%
    FileAppend, %str%, %file%
}

WriteDefaultExplorerInfo()
{
    file = %A_Temp%\ExplorerInfo.json
    WriteExplorerInfo(file)
}

Explorer_GetPath(hwnd="")
{
    if !(window := Explorer_GetWindow(hwnd))
        return
    if (window="desktop")
        return A_Desktop
    path := window.LocationURL
    path := RegExReplace(path, "ftp://.*@","ftp://")
    StringReplace, path, path, file:///
    StringReplace, path, path, /, \, All 
    
    ; thanks to polyethene
    Loop
        If RegExMatch(path, "i)(?<=%)[\da-f]{1,2}", hex)
        StringReplace, path, path, `%%hex%, % Chr("0x" . hex), All
    Else Break
        return path
}

Explorer_GetAll(hwnd="")
{
    return Explorer_Get(hwnd)
}

Explorer_GetSelected(hwnd="")
{
    return Explorer_Get(hwnd,true)
}

Explorer_GetWindow(hwnd="")
{
    ; thanks to jethrow for some pointers here
    WinGet, process, processName, % "ahk_id" hwnd := hwnd? hwnd:WinExist("A")
    WinGetClass class, ahk_id %hwnd%
    
    if (process!="explorer.exe")
        return
    if (class ~= "(Cabinet|Explore)WClass")
    {
        for window in ComObjCreate("Shell.Application").Windows
            if (window.hwnd==hwnd)
            return window
    }
    else if (class ~= "Progman|WorkerW") 
        return "desktop" ; desktop found
}

Explorer_Get(hwnd="",selection=false)
{
    ret := []
    
    if !(window := Explorer_GetWindow(hwnd))
        return []
    
    if (window="desktop")
    {
        ControlGet, hwWindow, HWND,, SysListView321, ahk_class Progman
        if !hwWindow ; #D mode
            ControlGet, hwWindow, HWND,, SysListView321, A
        ControlGet, files, List, % ( selection ? "Selected":"") "Col1",,ahk_id %hwWindow%
        base := SubStr(A_Desktop,0,1)=="\" ? SubStr(A_Desktop,1,-1) : A_Desktop
        Loop, Parse, files, `n, `r
        {
            path := base "\" A_LoopField
            IfExist %path% ; ignore special icons like Computer (at least for now)
                ret.Push(path)
        }
    }
    else
    {
        if selection
            collection := window.document.SelectedItems
        else
            collection := window.document.Folder.Items
        for item in collection
            ret.Push(item.path)
    }
    
    return ret
}