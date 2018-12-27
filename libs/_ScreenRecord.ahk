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

Record()
{
    global g_windowTitle
    if (g_windowTitle == "")
    {
        MsgBox g_windowTitle is not set
        ExitApp
    }
    
	WinActivate %g_windowTitle%
    WinWaitActive %g_windowTitle%
    if not WinGetClientPos(g_windowTitle, x, y, w, h)
    {
        MsgBox Cannot find window: %g_windowTitle%
        return false
    }
	
	; Start VLC
    WinClose ahk_exe vlc.exe
	FormatTime, now, R, yyyyMMdd_hhmmss
	fileOut = %A_MyDocuments%\Record_%now%.mp4
	commandLine = "C:\Program Files\VideoLAN\VLC\vlc.exe" screen:// :sout=#transcode{vcodec=h264,vb=0,scale=0,acodec=mpga,ab=128,channels=2,samplerate=44100}:file{dst=%fileOut%} :screen-fps=60 :screen-left=%x% :screen-top=%y% :screen-width=%w% :screen-height=%h%
    Run, %commandLine%,, Min
}

Stop()
{
    WinClose ahk_exe vlc.exe
}

Exit()
{
	Stop()
    ExitApp
}

SetKeyDelay, 10, 10
SetWorkingDir % A_Desktop
Hotkey, Esc, Exit