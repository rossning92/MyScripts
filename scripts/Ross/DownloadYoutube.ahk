#SingleInstance Force

SetWorkingDir %A_Desktop%

lastUrl := Clipboard
Loop {
    if ( lastUrl <> Clipboard and InStr(Clipboard, "https://www.youtube.com/watch") = 1 ) {
        lastUrl := Clipboard
        
        Run youtube-dl -f bestvideo+bestaudio %lastUrl%
    }
    Sleep 1000
}
