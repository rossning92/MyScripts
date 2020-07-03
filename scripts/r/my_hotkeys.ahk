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

#t::WinSet, AlwaysOnTop, Toggle, A

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
$XButton2::
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
        
        ; ResizeWindow("ahk_id " hwnd, x, y, w, h)
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
    ResizeWindow("A", (A_ScreenWidth/2)-(width/2), (A_ScreenHeight/2)-(height/2), width, height)
}

ToggleDesktopIcons() {
    ControlGet, HWND, Hwnd,, SysListView321, ahk_class WorkerW
    
    If DllCall("IsWindowVisible", UInt, HWND)
        WinHide, ahk_id %HWND%
    Else
        WinShow, ahk_id %HWND%
}

ResizeWindow(wintitle, X := "", Y := "", W := "", H := "") {
    WinGet hwnd, ID, %wintitle% ; WinExist() sets the last found window
    
    If ((X . Y . W . H) = "")
        Return False
    If !WinExist("ahk_id " . hwnd)
        Return False
    VarSetCapacity(WI, 60, 0) ; WINDOWINFO structure
    NumPut(60, WI, "Uint")
    If !DllCall("GetWindowInfo", "Ptr", hwnd, "Ptr", &WI)
        Return False
    WX := NumGet(WI, 4, "Int") ; X coordinate of the window
    WY := NumGet(WI, 8, "Int") ; Y coordinate of the window
    WW := NumGet(WI, 12, "Int") - WX ; width of the window
    WH := NumGet(WI, 16, "Int") - WY ; height of the window
    BW := NumGet(WI, 48, "UInt") - 1 ; border width - 1
    BH := NumGet(WI, 52, "UInt") - 1 ; border height - 1
    X := X <> "" ? X - BW : WX
    Y := Y <> "" ? Y : WY
    W := W <> "" ? W + BW + BW : WW
    H := H <> "" ? H + BH : WH
    
    
    DllCall("MoveWindow", "Ptr", hwnd, "Int", X, "Int", Y, "Int", W, "Int", H, "UInt", 1)
    WinRestore ahk_id %hwnd%
}