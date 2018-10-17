#SingleInstance Force

SetWorkingDir %A_Desktop%

lastUrl := Clipboard
Loop
{
    if ( lastUrl <> Clipboard)
	{
		if ( InStr(Clipboard, "https://www.youtube.com/watch") = 1 )
		{
			lastUrl := Clipboard
			Run youtube-dl -f bestvideo+bestaudio %lastUrl%
		}
        else if ( InStr(Clipboard, "https://www.bilibili.com/video/") = 1 )
		{
			lastUrl := Clipboard
			Run you-get --no-caption --playlist %lastUrl%
		}
    }
    Sleep 1000
}


