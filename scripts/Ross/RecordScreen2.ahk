SetWorkingDir %A_Desktop%


TITLE = ahk_exe notepad++.exe


WinGet, hwnd, ID, %TITLE%
WinGetClientPos(hwnd, x, y, w, h)
sizeParams = -offset_x %x% -offset_y %y% -video_size %w%x%h%

Run ffmpeg -y -f gdigrab -framerate 60 %sizeParams% -i desktop -c:v libx264 -crf 0 -preset ultrafast output.mkv

Sleep 1000
WinActivate, ahk_id %hwnd%


WinGetClientPos( Hwnd, ByRef x, ByRef y, ByRef w, ByRef h ) {
	VarSetCapacity( size, 16, 0 )
	DllCall( "GetClientRect", UInt, Hwnd, Ptr, &size )
	DllCall( "ClientToScreen", UInt, Hwnd, Ptr, &size )
	x := NumGet(size, 0, "Int")
	y := NumGet(size, 4, "Int")
	w := NumGet( size, 8, "Int" )
	h := NumGet( size, 12, "Int" )
}