SortArray(Array, Order="A") {
    ;Order A: Ascending, D: Descending, R: Reverse
    MaxIndex := ObjMaxIndex(Array)
    If (Order = "R") {
        count := 0
        Loop, % MaxIndex
            ObjInsert(Array, ObjRemove(Array, MaxIndex - count++))
        Return
    }
    Partitions := "|" ObjMinIndex(Array) "," MaxIndex
    Loop {
        comma := InStr(this_partition := SubStr(Partitions, InStr(Partitions, "|", False, 0)+1), ",")
        spos := pivot := SubStr(this_partition, 1, comma-1) , epos := SubStr(this_partition, comma+1) 
        if (Order = "A") { 
            Loop, % epos - spos {
                if (Array[pivot] > Array[A_Index+spos])
                    ObjInsert(Array, pivot++, ObjRemove(Array, A_Index+spos)) 
            }
        } else {
            Loop, % epos - spos {
                if (Array[pivot] < Array[A_Index+spos])
                    ObjInsert(Array, pivot++, ObjRemove(Array, A_Index+spos)) 
            }
        }
        Partitions := SubStr(Partitions, 1, InStr(Partitions, "|", False, 0)-1)
        if (pivot - spos) > 1 ;if more than one elements
            Partitions .= "|" spos "," pivot-1 ;the left partition
        if (epos - pivot) > 1 ;if more than one elements
            Partitions .= "|" pivot+1 "," epos ;the right partition
    } Until !Partitions
}

LayoutWindows(title, x="", y="", w="", h="", rows="")
{
    WinGet, id, List, %title%

    ; Convert peudo-array to array: hwnds.
    hwnds := []
    Loop, %id%
    {
        hwnds.Push(id%A_Index%)
    }
    SortArray(hwnds, "A")

    if (rows = "") {
        rows := Floor(Sqrt(hwnds.Length()))
    }
    cols := hwnds.Length() // rows

    if ( mod(hwnds.Length(), rows) > 0 )
        cols := cols + 1

    t := rows
    rows := cols
    cols := t

    SysGet, workArea, MonitorWorkArea
    if (x = "") {
        x := workAreaLeft
    }
    if (y = "") {
        y := workAreaTop
    }
    if (w = "") {
        w := workAreaRight - workAreaLeft
    }
    if (h = "") {
        h := workAreaBottom - workAreaTop
    }

    winWidth := w // cols
    winHeight := h // rows

    for index, hwnd in hwnds
    {
        i := (A_Index - 1) // cols
        j := mod(A_Index - 1, cols)
        winX := x + j * winWidth
        winY := y + i * winHeight
        SetWindowPos("ahk_id " hwnd, winX, winY, winWidth, winHeight)
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

SetWindowPos(WinTitle, X:="", Y:="", W:="", H:="", forceResize:=False) {
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
        WinSet, AlwaysOnTop, On, %windowTitle%
        ; WS_MAXIMIZEBOX 0x10000 + WS_MINIMIZEBOX 0x20000
        WinSet, Style, -0x30000, A
    }
    else
    {
        WinSet, AlwaysOnTop, Off, %windowTitle%
        WinSet, Style, +0x30000, A
    }
}