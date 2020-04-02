#NoTrayIcon
#SingleInstance, Force
#InstallKeybdHook
#include ../../libs/ahk/ExplorerHelper.ahk
#include ../../libs/ahk/ChromeHotkey.ahk

WindowList := {}

CONSOLE_WINDOW = MyScripts - Console
GUI_WINDOW = MyScripts - GUI

SetTitleMatchMode, 2

AddChromeHotkey("#!.", "- To Do", "https://to-do.microsoft.com/tasks")
AddChromeHotkey("#!m", "- Gmail", "https://mail.google.com/mail/u/0/#inbox")

return

#If WinActive("- Gmail ahk_exe chrome.exe")
    !r::
    Send *a
    Sleep 500
    Send +i
    Sleep 500
    Send *n
return
#If
    

#If WinActive("ahk_exe ConEmu64.exe")
Esc::
; KeyWait, Esc, U
; KeyWait, Esc, D T.3
; If ErrorLevel
; 	return

WinClose ahk_exe ConEmu64.exe
return
#If
    

#If not WinActive("ahk_exe vncviewer.exe") and not WinActive("ahk_exe League of Legends.exe")
    
!a::Run "C:\Program Files\Everything\Everything.exe" -toggle-window
#c::ActivateChrome(0)
#!c::ActivateChrome(2)
#!2::ActivateChrome(3)

^q::
    ; If explorer is active, copy file path to clipboard
    WriteExplorerInfoToJson()
    
    ; Activate script window
    if WinExist(CONSOLE_WINDOW) {
        WinActivate % CONSOLE_WINDOW
        WinActivate % GUI_WINDOW
    } else {
        WinActivate % GUI_WINDOW
    }
return

~LButton & WheelUp::
    Suspend, Permit
    SoundSet +5
    SoundPlay *16
return

~LButton & WheelDown::
    Suspend, Permit
    SoundSet -5
    SoundPlay *16
return

#F4::
    Suspend, Permit
    WinGet, pid, PID, A
    Process, Close, %pid%
    SoundPlay %BEEP_FILE%
return

!#F4::
    ; Close all explorer windows
    WinGet, winList, List, ahk_class CabinetWClass
    Loop, %winList%
    {
        this_id := winList%A_Index%
        WinClose, ahk_id %this_id%
    }
    
    ; Close "(Finished)" windows
    WinGet, winList, List, (Finished)
    Loop, %winList%
    {
        this_id := winList%A_Index%
        WinClose, ahk_id %this_id%
    }
return

+F1::
    Send {F1}
    WinWaitActive ahk_exe Snipaste.exe
    Send r
    Send ^+s
return

#v::
    WinActivate ahk_exe code.exe
return

#Left::
    UpdateWindowPosition("left")
return

#Right::
    UpdateWindowPosition("right")
return

#Up::
    WinMaximize, A
    WinSet, AlwaysOnTop, Off, A
return

#If
    

#If WinActive("ahk_exe vncviewer.exe")
F8::
Send {F8}
Send f
return
#If
    
ArrayHasValue(array, needle) {
    if not IsObject(array) {
        return false
    }
    for k, v in array {
        if (needle = v) {
            return true
        }
    }
    return false
}

UpdateWindowPosition(pos) {
    global WindowList
    
    WinGet, curHwnd, ID, A
    
    prevPos := ""
    for p, hwnd in WindowList {
        if (hwnd = curHwnd) {
            prevPos := p
            break
        }
    }
    
    if (prevPos != "") {
        ; If current window already in WindowList
        WindowList[prevPos] := WindowList[pos]   
    }
    WindowList[pos] := curHwnd
    
    WinGetPos,tx,ty,tw,th,ahk_class Shell_TrayWnd,,,
    RATIO := 2 / 3
    
    for pos, hwnd in WindowList {
        if (pos = "left") {
            x := 0
            w := Floor(A_ScreenWidth * RATIO)
        } else if (pos = "right")
        {
            x := Floor(A_ScreenWidth * RATIO)
            w := Floor(A_ScreenWidth * (1 - RATIO))
        }
        
        y := 0
        h := A_ScreenHeight - th
        
        WinRestore, ahk_id %hwnd%
        WinMove, ahk_id %hwnd%, , %x%, %y%, %w%, %h%
        if (hwnd != curHwnd) {
            WinActivate, ahk_id %hwnd%
        }
    }

    WinActivate, ahk_id %curHwnd%
}

ActivateChrome(index=0)
{
    if (index = 0)
    {
        condition := "NOT CommandLine LIKE '%--user-data-dir=%' AND NOT CommandLine LIKE '%--type=%'"
    }
    else
    {
        condition := "CommandLine LIKE '%ChromeData" index "%' AND NOT CommandLine LIKE '%--type=%'"
    }
    
    pid =
    for process in ComObjGet("winmgmts:").ExecQuery("SELECT * FROM Win32_Process WHERE Name='chrome.exe' AND " condition)
    {
        pid := process.ProcessID
        break
    }
    
    if ( pid != "" and WinExist("- Google Chrome ahk_pid " pid) )
    {
        WinActivate
    }
    else
    {
        if (index = 0)
        {
            Run chrome.exe
        }
        else
        {
            Run chrome.exe --user-data-dir=%USERPROFILE%\ChromeData%index%
        }
    }
}

MouseIsOverAndActive(title) {
    MouseGetPos,,, id
    if not WinActive("ahk_id " id)
        return false
    
    WinGet, matched_win_id, ID, %title%
    if (id = matched_win_id)
        return true
    else
        return false
}