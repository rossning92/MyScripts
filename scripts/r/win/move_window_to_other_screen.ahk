#SingleInstance Force

; https://www.autohotkey.com/boards/viewtopic.php?t=64784

#m::
MMPrimDPI := 1.0 ;DPI Scale of the primary monitor (divided by 100).
MMSecDPI := 1.0  ;DPI Scale of the secondary monitor (divided by 100).
SysGet, MMCount, MonitorCount
SysGet, MMPrimary, MonitorPrimary
SysGet, MMPrimLRTB, Monitor, MMPrimary
WinGetPos, MMWinGetX, MMWinGetY, MMWinGetWidth, MMWinGetHeight, A
MMWinGetXMiddle := MMWinGetX + (MMWinGetWidth / 2)
MMDPISub := Abs(MMPrimDPI - MMSecDPI) + 1
;Second mon is off, window is lost, bring to primary
if ( (MMCount = 1) and !((MMWinGetXMiddle > MMPrimLRTBLeft + 20) and (MMWinGetXMiddle < MMPrimLRTBRight - 20) and (MMWinGetY > MMPrimLRTBTop + 20) and (MMWinGetY < MMPrimLRTBBottom - 20)) ){
    if ((MMPrimDPI - MMSecDPI) >= 0)
        MMWHRatio := 1 / MMDPISub
    Else
        MMWHRatio := MMDPISub
    MMWinMoveWidth := MMWinGetWidth * MMWHRatio
    MMWinMoveHeight := MMWinGetHeight * MMWHRatio
    WinMove, A,, 0, 0, MMWinMoveWidth, MMWinMoveHeight
    WinMove, A,, 0, 0, MMWinMoveWidth, MMWinMoveHeight ;Fail safe
    return
}
if (MMPrimary = 1)
    SysGet, MMSecLRTB, Monitor, 2
Else
    SysGet, MMSecLRTB, Monitor, 1
MMSecW := MMSecLRTBRight - MMSecLRTBLeft
MMSecH := MMSecLRTBBottom - MMSecLRTBTop
;Primary to secondary
if ( (MMWinGetXMiddle > MMPrimLRTBLeft - 20) and (MMWinGetXMiddle < MMPrimLRTBRight + 20) and (MMWinGetY > MMPrimLRTBTop - 20) and (MMWinGetY < MMPrimLRTBBottom + 20) ){
    if ( (MMSecW) and (MMSecH) ){ ;Checks if sec mon exists. Could have used MMCount instead: if (MMCount >= 2){}
        if ((MMSecDPI - MMPrimDPI) >= 0){
            MMWidthRatio := (MMSecW / A_ScreenWidth) / MMDPISub
            MMHeightRatio := (MMSecH / A_ScreenHeight) / MMDPISub
        }
        Else {
            MMWidthRatio := (MMSecW / A_ScreenWidth) * MMDPISub
            MMHeightRatio := (MMSecH / A_ScreenHeight) * MMDPISub            
        }
        MMWinMoveX := (MMWinGetX * MMWidthRatio) + MMSecLRTBLeft
        MMWinMoveY := (MMWinGetY * MMHeightRatio) + MMSecLRTBTop
        if (MMSecLRTBBottom - MMWinMoveY < 82) ;Check if window is going under taskbar and fixes it.
            MMWinMoveY -= 82
        MMWinMoveWidth := MMWinGetWidth * MMWidthRatio
        MMWinMoveHeight := MMWinGetHeight * MMHeightRatio
        WinMove, A,, MMWinMoveX, MMWinMoveY, MMWinMoveWidth, MMWinMoveHeight
        WinMove, A,, MMWinMoveX, MMWinMoveY, MMWinMoveWidth, MMWinMoveHeight
    }
} ;Secondary to primary
Else if ( (MMWinGetXMiddle > MMSecLRTBLeft - 20) and (MMWinGetXMiddle < MMSecLRTBRight + 20) and (MMWinGetY > MMSecLRTBTop - 20) and (MMWinGetY < MMSecLRTBBottom + 20) ){
    if ( (MMSecW) and (MMSecH) ){
        if ((MMPrimDPI - MMSecDPI) >= 0){
            MMWidthRatio := (A_ScreenWidth / MMSecW) / MMDPISub
            MMHeightRatio := (A_ScreenHeight / MMSecH) / MMDPISub
        }
        Else{
            MMWidthRatio := (A_ScreenWidth / MMSecW) * MMDPISub
            MMHeightRatio := (A_ScreenHeight / MMSecH) * MMDPISub
        }
        MMWinMoveX := (MMWinGetX - MMSecLRTBLeft) * MMWidthRatio
        MMWinMoveY := (MMWinGetY - MMSecLRTBTop) * MMHeightRatio
        if (MMPrimLRTBBottom - MMWinMoveY < 82)
            MMWinMoveY -= 82
        MMWinMoveWidth := MMWinGetWidth * MMWidthRatio
        MMWinMoveHeight := MMWinGetHeight * MMHeightRatio
        WinMove, A,, MMWinMoveX, MMWinMoveY, MMWinMoveWidth, MMWinMoveHeight
        WinMove, A,, MMWinMoveX, MMWinMoveY, MMWinMoveWidth, MMWinMoveHeight
    }
} ;If window is out of current monitors' boundaries or if script fails
Else{
    MsgBox, 4, MM, % "Current window is in " MMWinGetX " " MMWinGetY "`nDo you want to move it to 0,0?"
    IfMsgBox Yes
    WinMove, A,, 0, 0
}
return