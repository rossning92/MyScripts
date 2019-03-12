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
				
				SetDownloadDir("Youtube")
                fmt = bestvideo+bestaudio
                
                Sleep 1000
                GetKeyState, keyState, Control
                if (keyState == "D")
                {
                    fmt = 134+140  ; 360p + audio
                    Msgbox Download 360p video format
                }
                
                Run cmd /c youtube-dl -f "%fmt%" %url% --no-mtime & timeout 10 
                
			}
			else if ( InStr(Clipboard, "https://www.bilibili.com/video/") = 1 )
			{
				g_lastUrl := Clipboard
				SetDownloadDir("Bilibili")
				Run cmd /c you-get --no-caption --playlist %g_lastUrl% & timeout 10
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