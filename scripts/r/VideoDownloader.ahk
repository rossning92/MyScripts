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
				
				SetDownloadDir("Youtube")
				Run youtube-dl -f bestvideo+bestaudio %g_lastUrl%
			}
			else if ( InStr(Clipboard, "https://www.bilibili.com/video/") = 1 )
			{
				g_lastUrl := Clipboard
				SetDownloadDir("Bilibili")
				Run you-get --no-caption --playlist %g_lastUrl%
			}
		}
	
	}
}

SetDownloadDir(dir)
{
	dir := A_Desktop "\" dir
	FileCreateDir %dir%
	SetWorkingDir %dir%
}