#Persistent
#SingleInstance, Force
#include <WaitKey>

SetTimer, CheckDownloads, 1000
return

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
