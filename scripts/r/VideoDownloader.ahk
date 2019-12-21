#SingleInstance Force
#Persistent

g_lastUrl := Clipboard
OnClipboardChange("ClipChanged")
return


ClipChanged(Type) {

	global g_lastUrl

	;  Contains something that can be expressed as text
	if (type = 1) {

		if ( g_lastUrl <> Clipboard)
		{
			if ( InStr(Clipboard, "https://www.youtube.com/watch") = 1 )
			{
				g_lastUrl := Clipboard
                url := SubStr(g_lastUrl, 1, 43)

				dir := GetDownloadDir("Youtube")

				key := WaitKey()
				if ( key = " " )
				{
					Run cmd /c youtube-dl -f bestvideo+bestaudio %url% --no-mtime & timeout 5, % dir
				}
				else if ( key = "v" )
				{
					Run cmd /c youtube-dl -f bestvideo[ext=mp4] %url% --no-mtime & timeout 5, % dir
				}
			}
			else if ( InStr(Clipboard, "https://www.bilibili.com/video/") = 1 )
			{
				g_lastUrl := Clipboard

				dir := GetDownloadDir("Bilibili")

				key := WaitKey()
				if ( key = " " )
				{
					Run cmd /c you-get --no-caption --playlist %g_lastUrl% & timeout 5, % dir
				}
			}
		}

	}
}

GetDownloadDir(dir)
{
	dir := A_Desktop "\" dir
	FileCreateDir %dir%
	return dir
}

WaitKey() {
	ToolTip, Press space to start downloading...
	Input, key, L1T10, {LControl}{RControl}{LAlt}{RAlt}{LShift}{RShift}{LWin}{RWin}{AppsKey}{F1}{F2}{F3}{F4}{F5}{F6}{F7}{F8}{F9}{F10}{F11}{F12}{Left}{Right}{Up}{Down}{Home}{End}{PgUp}{PgDn}{Del}{Ins}{BS}{CapsLock}{NumLock}{PrintScreen}{Pause}
	ToolTip
	return key
}