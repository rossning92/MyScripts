#SingleInstance Force


lastUrl := Clipboard
Loop
{
    if ( lastUrl <> Clipboard)
	{
		if ( InStr(Clipboard, "https://www.youtube.com/watch") = 1 )
		{
			lastUrl := Clipboard
			
			SetDownloadDir("Youtube")
			Run youtube-dl -f bestvideo+bestaudio %lastUrl%
		}
        else if ( InStr(Clipboard, "https://www.bilibili.com/video/") = 1 )
		{
			lastUrl := Clipboard
			SetDownloadDir("Bilibili")
			Run you-get --no-caption --playlist %lastUrl%
		}
    }
    Sleep 1000
}


SetDownloadDir(dir)
{
	dir := A_Desktop "\" dir
	FileCreateDir %dir%
	SetWorkingDir %dir%
}