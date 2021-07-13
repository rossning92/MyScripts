#SingleInstance, Force
#InstallKeybdHook
#include ../../ahk/ExplorerHelper.ahk
#include ../../ahk/ChromeHotkey.ahk
#include ../../ahk/VirtualDesktop.ahk
#include ../../ahk/Window.ahk
#include ../../ahk/WinDrag.ahk

SetCapsLockState, AlwaysOff

WindowList := {}
CurrentDesktop := 0
WindowDividor := 2/3

CONSOLE_WINDOW = my_scripts_console

SetTitleMatchMode, 2

AddChromeHotkey("#!.", "- To Do", "https://to-do.live.com/tasks/")
AddChromeHotkey("#!m", "- Gmail", "https://mail.google.com/mail/u/0/#inbox")

SetTimer, CheckIfRShiftIsPressed, 1000

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

#If not WinActive("ahk_exe tvnviewer.exe") and not WinActive("ahk_exe vncviewer.exe") and not WinActive("ahk_exe League of Legends.exe")

#LButton::WindowMouseDragMove()

!a::Run "C:\Program Files\Everything\Everything.exe" -toggle-window
#c::ActivateChrome(0)
#!c::ActivateChrome(2)
#!2::ActivateChrome(3)
#m::ToggleMicrophone()

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
    if not WinExist("ahk_exe code.exe") {
        EnvGet, LocalAppData, LocalAppData
        Run %LocalAppData%\Programs\Microsoft VS Code\Code.exe
    } else {
        ActivateWindowByTitle("ahk_exe code.exe")
    }
return

#Left::
    UpdateWindowPosition("left")
return

#Right::
    UpdateWindowPosition("right")
return

#t::
    WinSet, AlwaysOnTop, Toggle, A
    WinGet, ExStyle, ExStyle, A
    If (ExStyle & 0x8) {
        ToolTip, AlwaysOnTop=1, 0, 0
    } else {
        ToolTip, AlwaysOnTop=0, 0, 0
    }
    SetTimer, RemoveToolTip, -2000
return

RemoveToolTip:
    ToolTip
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

$!`::
    if (WindowDividor = 2/3) {
        WindowDividor := 1/2

    } else {
        WindowDividor := 2/3
    }
return

$!1::
    if WinActive("ahk_exe FL64.exe") {
        SetWindowPosF("A", 0, 0, WindowDividor, 1, False, True)
    } else {
        SetWindowPosF("A", 0, 0, WindowDividor, 1)
    }
    WinSet, AlwaysOnTop, Off, A
return

$!2::
    SetWindowPosF("A", WindowDividor, 0, 1-WindowDividor, 1)
    WinSet, AlwaysOnTop, On, A
return

$!3::
    SetWindowPos("A", 0, 0, 1920, 1080, forceResize:=True)
    WinSet, AlwaysOnTop, Off, A
return

$!4::
    SetWindowPos("A", 0, 0, 1440, 810)
    WinSet, AlwaysOnTop, Off, A
return

$!5::
    SetWindowPos("A", 240, 135, 1440, 810)
    WinSet, AlwaysOnTop, Off, A
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

        WinSet, AlwaysOnTop, Off, ahk_id %hwnd%

        SetWindowPos("ahk_id " hwnd, x, y, w, h)
        if (hwnd != curHwnd) {
            WinActivate, ahk_id %hwnd%
        }
    }

    WinActivate, ahk_id %curHwnd%
}

UpdateActiveWindowPosition() {
    global WindowList

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

    title := "- Google Chrome ahk_pid " pid
    if ( pid != "" and WinExist(title) )
    {
        ActivateWindowByTitle(title)
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
    ; x := 0, y := 0

    w := A_ScreenHeight * 16 / 9
    h := A_ScreenHeight
    x := (A_ScreenWidth - w) / 2
    y := 0
    SetWindowPos("A", x, y, w, h)
}

SetWindowPos3(wintitle, X := "", Y := "", W := "", H := "") {
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
    VNC_VIEWER := "ahk_exe vncviewer.exe"

    if WinActive("ahk_exe tvnviewer.exe") {
        WinMinimize, ahk_exe tvnviewer.exe
    } else if WinActive(VNC_VIEWER) {
        WinMinimize, %VNC_VIEWER%
        WinSet, AlwaysOnTop, Off, %VNC_VIEWER%
    } else if WinExist("ahk_exe tvnviewer.exe") {
        WinActivate, ahk_exe tvnviewer.exe
    } else if WinExist(VNC_VIEWER) {
        WinActivate, %VNC_VIEWER%
        SetWindowPosF(VNC_VIEWER, 0, 0, 32/43, 1, true, true)
        WinSet, AlwaysOnTop, On, %VNC_VIEWER%
    }
}

CheckIfRShiftIsPressed()
{
    if (GetKeyState("RShift", "P"))
    {
        ToggleVNC()
    }
}

ToggleMicrophone()
{
    global Muted
    if (Muted)
    {
        ToolTip
        Run powershell -NoProfile -ExecutionPolicy unrestricted audio/unmute_mic.ps1,, Hide
        Muted := false
    }
    else
    {
        ToolTip, [MUTED], 0, 0
        Run powershell -NoProfile -ExecutionPolicy unrestricted audio/mute_mic.ps1,, Hide
        Muted := true
    }
}

#include win/change_screen_resolution.ahk
