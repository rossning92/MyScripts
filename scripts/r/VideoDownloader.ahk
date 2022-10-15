#SingleInstance Force
#Persistent

DownloadDir := "{{VIDEO_DOWNLOAD_DIR}}"
OnClipboardChange("ClipChanged")
return

ClipChanged(type) {
    global DownloadDir

    if (type = 1) { ; clipboard has text
        text := Clipboard
        Loop, parse, text, `n, `r ; for each line
        {
            line := A_LoopField
            if (RegExMatch(line, "https?://((www\.)?bilibili\.com/video/)|(www.youtube.com/watch)")) {
                g_lastUrl := line
                key := WaitKey("space - download video`nv - download video to desktop`na - download audio to desktop")
                if (key = "v") {
                    Run, cmd /c run_script r/download_video.py "%line%" --download_dir "%A_Desktop%" & timeout 5
                } else if (key = "a") {
                    Run, cmd /c run_script r/download_video.py --audio_only "%line%" --download_dir "%A_Desktop%" & timeout 5
                } else if (key = " ") {
                    Run, cmd /c run_script r/download_video.py "%line%" & timeout 5
                }
            } else if (RegExMatch(line, "^aria2c ")) {
                if (A_Index = 1) {
                    key := WaitKey("space - start download")
                    if (key <> " ") {
                        return
                    }
                }
                Run, cmd /c %line% & timeout 5, % DownloadDir
            }
        }

    }
}

WaitKey(prompt) {
    ToolTip, %prompt%
    Input, key, L1T10, {LButton}{RButton}{MButton}{LControl}{RControl}{LAlt}{RAlt}{LShift}{RShift}{LWin}{RWin}{AppsKey}{F1}{F2}{F3}{F4}{F5}{F6}{F7}{F8}{F9}{F10}{F11}{F12}{Left}{Right}{Up}{Down}{Home}{End}{PgUp}{PgDn}{Del}{Ins}{BS}{CapsLock}{NumLock}{PrintScreen}{Pause}
    ToolTip
    return key
}
