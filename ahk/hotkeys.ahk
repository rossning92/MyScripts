#SingleInstance, Force

^q::
    if WinExist("MyScripts - GUI")
        WinActivate MyScripts - GUI
    else
        WinActivate MyScripts - Console