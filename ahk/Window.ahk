LayoutWindows(title)
{
    WinGet, winList, List, %title%
    n := winList

    rows := Floor(Sqrt(n))
    cols := n // rows

    if ( mod(n, rows) > 0 )
        cols := cols + 1

    t := rows
    rows := cols
    cols := t

    SysGet, workArea, MonitorWorkArea
    width := (workAreaRight - workAreaLeft) // cols
    height := (workAreaBottom - workAreaTop) // rows

    Loop, %winList%
    {
        this_id := winList%A_Index%

        i := (A_Index - 1) // cols
        j := mod(A_Index - 1, cols)

        x := workAreaLeft + j * width
        y := workAreaTop + i * height

        ; Msgbox %x%|%y%|%width%|%height%

        WinRestore, ahk_id %this_id%
        WinActivate, ahk_id %this_id%
        WinMove ahk_id %this_id%,, %x%, %y%, %width%, %height%
    }
}

CloseWindows(title)
{
    WinGet, winList, List, %title%
    Loop, %winList%
    {
        this_id := winList%A_Index%
        WinClose, ahk_id %this_id%
    }
}

SetWindowPosF(winTitle, x, y, w, h, fullScreen:=False, forceResize:=False) {
    SysGet, wa, MonitorWorkArea

    width := waRight - waLeft
    height := waBottom - waTop

    if (fullScreen) {
        width := A_ScreenWidth
        height := A_ScreenHeight
    }

    x := round(width * x)
    y := round(height * y)
    w := round(width * w)
    h := round(height * h)

    SetWindowPos(winTitle, x, y, w, h, forceResize)
}

SetWindowPos(WinTitle, X := "", Y := "", W := "", H := "", forceResize := False) {
    If ((X . Y . W . H) = "") ;
        Return False
    WinGet, hWnd, ID, %WinTitle% ; taken from Coco's version
    WinRestore, ahk_id %hWnd%
    WinActivate, ahk_id %hWnd%
    If !(hWnd)
        Return False
    deltaLeft := deltaTop := deltaRight := deltaBottom := 0
    VarSetCapacity(rect, 16, 0)
    DllCall("GetWindowRect", "Ptr", hWnd, "Ptr", &rect)
    winLeft := NumGet(rect, 0, "Int")
    winTop := NumGet(rect, 4, "Int")
    winRight := NumGet(rect, 8, "Int")
    winBottom := NumGet(rect, 12, "Int")
    If (DllCall("Dwmapi.dll\DwmGetWindowAttribute", "Ptr", hWnd, "UInt", 9, "Ptr", &rect, "UInt", 16) = 0) { ; S_OK = 0
        frameLeft := NumGet(rect, 0, "Int")
        frameTop := NumGet(rect, 4, "Int")
        frameRight := NumGet(rect, 8, "Int")
        frameBottom := NumGet(rect, 12, "Int")

        deltaLeft := winLeft - frameLeft
        deltaTop := winTop - frameTop
        deltaRight := winRight - frameRight
        deltaBottom := winBottom - frameBottom
    }
    X := X <> "" ? X + deltaLeft : winLeft
    Y := Y <> "" ? Y + deltaTop : winTop
    W := W <> "" ? W - deltaLeft + deltaRight : winRight - winLeft
    H := H <> "" ? H - deltaTop + deltaBottom : winBottom - winTop

    WS_SIZEBOX = 0x40000
    WinGet, Style, Style, A
    if (forceResize or (Style & WS_SIZEBOX)) {
        Return DllCall("MoveWindow", "Ptr", hWnd, "Int", X, "Int", Y, "Int", W, "Int", H, "UInt", 1)
    } else {
        X := X + (W - (winRight - winLeft)) / 2
        Y := Y + (H - (winBottom - winTop)) / 2
        WinMove, ahk_id %hWnd%,, %X%, %Y%
    }
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

ActivateWindowByTitle(title)
{
    WinGet, hwnds, List, %title%

    Loop % hwnds
    {
        hwnd := hwnds%A_Index%

        WinGet, style, Style, ahk_id %hwnd%

        ; Skip unimportant window
        if (style & WS_DISABLED) 
            continue

        ; Skip window with no title
        WinGetTitle, title, ahk_id %hwnd%
        if not title
            continue

        ; Skip active window
        if WinActive("ahk_id " hwnd)
            continue

        ; Skip top most window
        WinGet, style, ExStyle, ahk_id %hwnd%
        if (style & 0x8)
            continue

        WinActivate ahk_id %hwnd%

        return
    }
}

SetAlwaysOnTop(windowTitle, onTop:=True)
{
    if (onTop)
    {
        WinSet, AlwaysOnTop, Off, %windowTitle%
        ; WS_MAXIMIZEBOX 0x10000 + WS_MINIMIZEBOX 0x20000
        WinSet, Style, +0x30000, A
    }
    else
    {
        WinSet, AlwaysOnTop, On, %windowTitle%
        WinSet, Style, -0x30000, A
    }
}