#NoTrayIcon
#SingleInstance, Force
#InstallKeybdHook
#include ../../libs/ahk/ExplorerHelper.ahk
#include ../../libs/ahk/ChromeHotkey.ahk

SetCapsLockState, AlwaysOff

WindowList := {}

CONSOLE_WINDOW = MyScripts - Console
GUI_WINDOW = MyScripts - GUI

SetTitleMatchMode, 2

AddChromeHotkey("#!.", "- To Do", "https://to-do.microsoft.com/tasks")
AddChromeHotkey("#!m", "- Gmail", "https://mail.google.com/mail/u/0/#inbox")

WinGet, LastWindowHwnd, ID, A
SetTimer, ReinstallKeyHooks, 2000
return

ReinstallKeyHooks:
    If (WinActive("ahk_exe tvnviewer.exe")) {
        Reload
    }
return

*CapsLock::Send {LWin Down}{LCtrl Down}
*CapsLock Up::Send {LWin Up}{LCtrl Up}

~LButton & WheelUp::
    Suspend, Permit
    SoundSet +2
    SoundPlay *16
return

~LButton & WheelDown::
    Suspend, Permit
    SoundSet -2
    SoundPlay *16
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
    

#If not WinActive("ahk_exe tvnviewer.exe") and not WinActive("ahk_exe League of Legends.exe")
    
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

$F1::
    Send ^{PrintScreen}
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
    WinGet, curHwnd, ID, A
    WinMaximize, ahk_id %curHwnd%
    WinSet, AlwaysOnTop, Off, ahk_id %curHwnd%
    
    for p, hwnd in WindowList {
        if (hwnd = curHwnd) {
            WindowList.Delete(p)
            break
        }
    }
return

#1::
    CenterActiveWindow()
return

#2::
    CenterActiveWindow(width:=1440, height:=810)
return

!#d::
    ToggleDesktopIcons()
return

#If
    
#If WinExist("ahk_exe tvnviewer.exe")
$F11::
if WinActive("ahk_exe tvnviewer.exe") {
    WinMinimize, ahk_exe tvnviewer.exe
} else {
    WinActivate, ahk_exe tvnviewer.exe
}
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
        WinSet, Style, +0x40000, ahk_id %hwnd%
        WinSet, Style, +Resize, ahk_id %hwnd%
        
        if (pos = "right")
        {
            WinSet, AlwaysOnTop, On, ahk_id %hwnd%
        }
        else
        {
            WinSet, AlwaysOnTop, Off, ahk_id %hwnd%
        }
        
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

CenterActiveWindow(width:=1920, height:=1080) {
    ; WinGetPos,,, width, height, A
    WinMove, A,, (A_ScreenWidth/2)-(width/2), (A_ScreenHeight/2)-(height/2), width, height
}

ToggleDesktopIcons() {
    ControlGet, HWND, Hwnd,, SysListView321, ahk_class WorkerW
    
    If DllCall("IsWindowVisible", UInt, HWND)
        WinHide, ahk_id %HWND%
    Else
        WinShow, ahk_id %HWND%
}
