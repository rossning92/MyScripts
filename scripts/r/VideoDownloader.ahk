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
            if ( RegExMatch(Clipboard, "https?://((www\.)?bilibili\.com/video/)|(www.youtube.com/watch)") )
            {
                g_lastUrl := Clipboard
                key := WaitKey()
                if ( key = " " )
                {
                    Run, cmd /c %A_ScriptDir%\..\..\bin\run_script.exe /r/download_video "%g_lastUrl%" & timeout 5, % dir, Min
                }
            }
        }

    }
}

WaitKey() {
    ToolTip, Press space to start downloading...
    Input, key, L1T10, {LControl}{RControl}{LAlt}{RAlt}{LShift}{RShift}{LWin}{RWin}{AppsKey}{F1}{F2}{F3}{F4}{F5}{F6}{F7}{F8}{F9}{F10}{F11}{F12}{Left}{Right}{Up}{Down}{Home}{End}{PgUp}{PgDn}{Del}{Ins}{BS}{CapsLock}{NumLock}{PrintScreen}{Pause}
    ToolTip
    return key
}