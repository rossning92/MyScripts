#SingleInstance, Force
#InstallKeybdHook
#include ../../libs/ahk/ExplorerHelper.ahk
#include ../../libs/ahk/ChromeHotkey.ahk
#include ../../libs/ahk/VirtualDesktop.ahk

SetCapsLockState, AlwaysOff

WindowList := {}
CurrentDesktop := 0

CONSOLE_WINDOW = my_scripts_console

SetTitleMatchMode, 2

AddChromeHotkey("#!.", "- To Do", "https://to-do.microsoft.com/tasks")
AddChromeHotkey("#!m", "- Gmail", "https://mail.google.com/mail/u/0/#inbox")

SetTimer, CheckIfRShiftIsPressed, 1000

return

AutoUpdateWindowPos()
{
    ; UpdateWindowPosition("left")
    ; UpdateWindowPosition("left")
    UpdateActiveWindowPosition()
}

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
    

#If not WinActive("ahk_exe tvnviewer.exe") and not WinActive("ahk_exe vncviewer.exe") and not WinActive("ahk_exe League of Legends.exe")
    
!a::Run "C:\Program Files\Everything\Everything.exe" -toggle-window
#c::ActivateChrome(0)
#!c::ActivateChrome(2)
#!2::ActivateChrome(3)

^q::
    ; If explorer is active, copy file path to clipboard
    UpdateExplorerInfo()
    
    ; Activate script window
    if WinExist(CONSOLE_WINDOW) {
        WinActivate % CONSOLE_WINDOW
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
    ; SetTimer, AutoUpdateWindowPos, 500
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
    
    SetTimer, AutoUpdateWindowPos, Off
return

#1::
    CenterActiveWindow()
return

#2::
    CenterActiveWindow(width:=1440, height:=810)
return

#3::
    ResizeWindow2("A", 0, 0, 1632, 918)
return

#0::
    CurrentDesktop := 1 - CurrentDesktop
    SwitchDesktopByNumber(CurrentDesktop + 1)
    ToggleDesktopIcons(1 - CurrentDesktop)
return

!#d::
    ToggleDesktopIcons()
return

#If
    
#If WinExist("ahk_exe tvnviewer.exe") or WinExist("ahk_exe vncviewer.exe")
$XButton2::
ToggleVNC()
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
        
        ResizeWindow2("ahk_id " hwnd, x, y, w, h)
        if (hwnd != curHwnd) {
            WinActivate, ahk_id %hwnd%
        }
    }
    
    WinActivate, ahk_id %curHwnd%
}

UpdateActiveWindowPosition() {
    global WindowList
    
    ; If right window was closed.
    if not WinExist("ahk_id " WindowList["right"]) {
        SetTimer, AutoUpdateWindowPos, Off
    }
    
    WinGet, cur_hwnd, ID, A
    
    ControlGet, HWND, hwnd,, SysListView321, ahk_class WorkerW
    if (hwnd = cur_hwnd) {
        return
    }
    
    WinGetClass, win_class, ahk_id %hwnd%
    if (win_class = "Windows.UI.Core.CoreWindow") {
        return
    }
    
    if (win_class = "Shell_TrayWnd") {
        return
    }
    
    for pos, hwnd in WindowList {
        if (hwnd = cur_hwnd and pos = "right") {
            return
        }
    }
    
    WinGetPos,tx,ty,tw,th,ahk_class Shell_TrayWnd,,,
    RATIO := 2 / 3
    w := Floor(A_ScreenWidth * RATIO)
    x := 0
    y := 0
    h := A_ScreenHeight - th
    
    WinRestore, ahk_id %cur_hwnd%
    WinSet, Style, +0x40000, ahk_id %cur_hwnd%
    WinSet, Style, +Resize, ahk_id %cur_hwnd%
    
    WinMove, ahk_id %cur_hwnd%, , %x%, %y%, %w%, %h%
}

ActivateChrome(index=0)
{
    CHROME_DIR := "C:\Program Files (x86)\Google\Chrome\Application"
    if (not FileExist(CHROME_DIR))
    {
        CHROME_DIR := "C:\Program Files\Google\Chrome\Application"
    }
    
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
            Run %CHROME_DIR%\chrome.exe, %CHROME_DIR%
        }
        else
        {
            Run %CHROME_DIR%\chrome.exe --user-data-dir=%USERPROFILE%\ChromeData%index%, %CHROME_DIR%
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
    x := (A_ScreenWidth / 2) - (width / 2)
    y := (A_ScreenHeight / 2) - (height / 2)
    x := 0, y := 0
    ResizeWindow2("A", x, y, width, height)
}

ToggleDesktopIcons(show:=True) {
    ; ahk_class WorkerW
    ControlGet, HWND, Hwnd,, SysListView321, ahk_class Progman
    
    if ( not DllCall("IsWindowVisible", UInt, HWND) or show ) {
        WinShow, ahk_id %HWND%
    } else {
        WinHide, ahk_id %HWND%
    }
}

ResizeWindow2(WinTitle, X := "", Y := "", W := "", H := "") {
    If ((X . Y . W . H) = "") ;
        Return False
    WinGet, hWnd, ID, %WinTitle% ; taken from Coco's version
    WinRestore, ahk_id %hWnd%
    If !(hWnd)
        Return False
    DL := DT := DR := DB := 0
    VarSetCapacity(RC, 16, 0)
    DllCall("GetWindowRect", "Ptr", hWnd, "Ptr", &RC)
    WL := NumGet(RC, 0, "Int"), WT := NumGet(RC, 4, "Int"), WR := NumGet(RC, 8, "Int"), WB := NumGet(RC, 12, "Int")
    If (DllCall("Dwmapi.dll\DwmGetWindowAttribute", "Ptr", hWnd, "UInt", 9, "Ptr", &RC, "UInt", 16) = 0) { ; S_OK = 0
        FL := NumGet(RC, 0, "Int"), FT := NumGet(RC, 4, "Int"), FR := NumGet(RC, 8, "Int"), FB := NumGet(RC, 12, "Int")
        DL := WL - FL, DT := WT - FT, DR := WR - FR, DB := WB - FB
    }
    X := X <> "" ? X + DL : WL, Y := Y <> "" ? Y + DT : WT
    W := W <> "" ? W - DL + DR : WR - WL, H := H <> "" ? H - DT + DB: WB - WT
    Return DllCall("MoveWindow", "Ptr", hWnd, "Int", X, "Int", Y, "Int", W, "Int", H, "UInt", 1)
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

ToggleVNC()
{
    if WinActive("ahk_exe tvnviewer.exe") {
        WinMinimize, ahk_exe tvnviewer.exe
    } else if WinActive("ahk_exe vncviewer.exe") {
        WinMinimize, ahk_exe vncviewer.exe
    } else if WinExist("ahk_exe tvnviewer.exe") {
        WinActivate, ahk_exe tvnviewer.exe
    } else if WinExist("ahk_exe vncviewer.exe") {
        WinActivate, ahk_exe vncviewer.exe
    }
}

CheckIfRShiftIsPressed()
{
    if (GetKeyState("RShift", "P"))
    {
        ToggleVNC()
    }
}

#include win/change_screen_resolution.ahk
