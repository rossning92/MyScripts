#SingleInstance Force

WinGetClientPos( winTitle, ByRef x, ByRef y, ByRef w, ByRef h )
{
    WinGet, hwnd, ID, %winTitle%
	VarSetCapacity( size, 16, 0 )
	DllCall( "GetClientRect", UInt, hwnd, Ptr, &size )
	DllCall( "ClientToScreen", UInt, hwnd, Ptr, &size )
	x := NumGet(size, 0, "Int")
	y := NumGet(size, 4, "Int")
	w := NumGet( size, 8, "Int" )
	h := NumGet( size, 12, "Int" )
}

WinGetClientPos("Oculus Mirror", x, y, w, h)
Run "C:\Program Files (x86)\VideoLAN\VLC\vlc.exe" screen:// :screen-fps=24 :screen-left=%x% :screen-top=%y% :screen-width=%w% :screen-height=%h%

F7::
    SetKeyDelay, 10, 10
    ControlSend,, +r{Shift Up}, ahk_exe vlc.exe
    return
    
Esc::
    ExitApp
    return