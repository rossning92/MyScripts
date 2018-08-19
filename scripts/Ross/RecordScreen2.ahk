SetWorkingDir %A_Desktop%
Gui -DPIScale

WinGetPos, x, y, w, h, ahk_exe notepad++.exe

SIZE = -offset_x %x% -offset_y %y% -video_size %w%x%h%

Run cmd /c ffmpeg -f gdigrab -framerate 60 %SIZE% -i desktop -c:v libx264 -crf 0 -preset ultrafast output.mkv