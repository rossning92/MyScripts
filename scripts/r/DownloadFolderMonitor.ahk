#Persistent
#SingleInstance, Force
#include <WaitKey>

LastModifiedTime := A_Now

CheckDownloads() {
    global LastModifiedTime

    DownloadPath = C:\Users\%A_UserName%\Downloads
    Loop, %DownloadPath%\*.*
    {
        if (A_LoopFileTimeModified > LastModifiedTime)
        {
            LastModifiedTime := A_LoopFileTimeModified

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
        }
    }
}

loop {
    CheckDownloads()
    Sleep 1000
}