#Persistent
#SingleInstance, Force
SetTimer, CheckDownloads, 1000
return

WaitKey(prompt) {
    CoordMode, ToolTip, Screen
    xpos := A_ScreenWidth // 2
    ypos := A_ScreenHeight // 2
    ToolTip, %prompt%, %xpos%, %ypos%
    Input, key, L1T10, {LButton}{RButton}{MButton}{LControl}{RControl}{LAlt}{RAlt}{LShift}{RShift}{LWin}{RWin}{AppsKey}{F1}{F2}{F3}{F4}{F5}{F6}{F7}{F8}{F9}{F10}{F11}{F12}{Left}{Right}{Up}{Down}{Home}{End}{PgUp}{PgDn}{Del}{Ins}{BS}{CapsLock}{NumLock}{PrintScreen}{Pause}
    ToolTip
    return key
}

CheckDownloads() {
    DownloadPath = C:\Users\%A_UserName%\Downloads
    Loop, %DownloadPath%\*.*
    {
        delta := A_Now
        EnvSub, delta, %A_LoopFileTimeModified%, Seconds
        if (delta < 2)
        {
            if (A_LoopFileExt = "crdownload")
            {
                continue
            }

            if (A_LoopFileExt = "zip" or A_LoopFileExt = "gz")
            {
                key := WaitKey("Press 1 to unzip: " A_LoopFileFullPath)
                if (key = "1") {
                    Run, run_script r/unzip.py --open "%A_LoopFileFullPath%"
                }
            }
            else if (A_LoopFileExt = "apk")
            {
                key := WaitKey("Press 1 to sideload: " A_LoopFileFullPath)
                if (key = "1") {
                    Run, cmd /c run_script r/android/install_apk.py --force_reinstall "%A_LoopFileFullPath%" & timeout 3
                }
            }
            break
        }
    }
}
