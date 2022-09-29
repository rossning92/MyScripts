#SingleInstance, Force

#include <Window>

VNC_VIEWER = "C:\Program Files\RealVNC\VNC Viewer\vncviewer.exe"

if WinExist("ahk_class vwr::CDesktopWin")
{
    WinActivate, ahk_class vwr::CDesktopWin
    return
}

Run, %VNC_VIEWER% {{VNC_SERVER}} -WarnUnencrypted=0 -PasswordStoreOffer=1 -FullScreen=1

WinWait, Authentication ahk_exe vncviewer.exe,, 3
if ErrorLevel
{
    return
}

Send, {{VNC_PASSWORD}}
Send, {Enter}

WinWait ahk_class vwr::CDesktopWin
SetWindowPos("A", 0, 0, A_ScreenHeight*16/9, A_ScreenHeight, true)
WinSet, AlwaysOnTop, On, A
