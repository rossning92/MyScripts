#SingleInstance Force

WinGetClientPos( winTitle, ByRef x, ByRef y, ByRef w, ByRef h )
{
    WinGet, hwnd, ID, %winTitle%
    if hwnd =
    {
        return false
    }    
    
	VarSetCapacity( size, 16, 0 )
	DllCall( "GetClientRect", UInt, hwnd, Ptr, &size )
	DllCall( "ClientToScreen", UInt, hwnd, Ptr, &size )
	x := NumGet(size, 0, "Int")
	y := NumGet(size, 4, "Int")
	w := NumGet( size, 8, "Int" )
	h := NumGet( size, 12, "Int" )
    return true
}

SetWindow(windowTitle)
{
    global g_windowTitle
    g_windowTitle := windowTitle
}

InitVLC()
{
    global g_windowTitle
    if (g_windowTitle == "")
    {
        MsgBox g_windowTitle is not set
        return false
    }
    
    ; Start VLC
    if not WinGetClientPos(g_windowTitle, x, y, w, h)
    {
        MsgBox Cannot find window: %g_windowTitle%
        return false
    }
    WinClose ahk_exe vlc.exe
    Run "C:\Program Files (x86)\VideoLAN\VLC\vlc.exe" screen:// :screen-fps=60 :screen-left=%x% :screen-top=%y% :screen-width=%w% :screen-height=%h%
    WinWaitActive, ahk_exe vlc.exe
    Sleep 1000
    
    return true
}

Record()
{
    global g_windowTitle

    Process, Exist, vlc.exe
    if (ErrorLevel = 0)
        if not InitVLC()
            return
    
    WinActivate %g_windowTitle%
    WinWaitActive %g_windowTitle%
    
    ControlSend,, +r{Shift Up}, ahk_exe vlc.exe
}

Exit()
{
    ExitApp
}

SetKeyDelay, 10, 10
SetWorkingDir % A_Desktop
Hotkey, F7, Record
Hotkey, Esc, Exit