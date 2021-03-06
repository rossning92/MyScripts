; Globals
_DesktopCount = 2 ; Windows starts with 2 desktops at boot
_CurrentDesktop = 1 ; Desktop count is 1-indexed (Microsoft numbers them this way)
;
; This function examines the registry to build an accurate list of the current virtual desktops and which one we're currently on.
; Current desktop UUID appears to be in HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\SessionInfo\1\VirtualDesktops
; List of desktops appears to be in HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\VirtualDesktops
;
MapDesktopsFromRegistry() {
    global _CurrentDesktop, _DesktopCount
    ; Get the current desktop UUID. Length should be 32 always, but there's no guarantee this couldn't change in a later Windows release so we check.
    IdLength := 32
    SessionId := GetSessionId()
    if (SessionId) {
        RegRead, CurrentDesktopId, HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\SessionInfo\%SessionId%\VirtualDesktops, CurrentVirtualDesktop
        if (CurrentDesktopId) {
            IdLength := StrLen(CurrentDesktopId)
        }
    }
    ; Get a list of the UUIDs for all virtual desktops on the system
    RegRead, DesktopList, HKEY_CURRENT_USER, SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\VirtualDesktops, VirtualDesktopIDs
    if (DesktopList) {
        DesktopListLength := StrLen(DesktopList)
        ; Figure out how many virtual desktops there are
        _DesktopCount := DesktopListLength / IdLength
    }
    else {
        _DesktopCount := 1
    }
    ; Parse the REG_DATA string that stores the array of UUID's for virtual desktops in the registry.
    i := 0
    while (CurrentDesktopId and i < _DesktopCount) {
        StartPos := (i * IdLength) + 1
        DesktopIter := SubStr(DesktopList, StartPos, IdLength)
        OutputDebug, The iterator is pointing at %DesktopIter% and count is %i%.
        ; Break out if we find a match in the list. If we didn't find anything, keep the
        ; old guess and pray we're still correct :-D.
        if (DesktopIter = CurrentDesktopId) {
            _CurrentDesktop := i + 1
            OutputDebug, Current desktop number is %_CurrentDesktop% with an ID of %DesktopIter%.
            break
        }
        i++
    }
}
;
; This functions finds out ID of current session.
;
GetSessionId()
{
    ProcessId := DllCall("GetCurrentProcessId", "UInt")
    if ErrorLevel {
        OutputDebug, Error getting current process id: %ErrorLevel%
        return
    }
    OutputDebug, Current Process Id: %ProcessId%
    DllCall("ProcessIdToSessionId", "UInt", ProcessId, "UInt*", SessionId)
    if ErrorLevel {
        OutputDebug, Error getting session id: %ErrorLevel%
        return
    }
    OutputDebug, Current Session Id: %SessionId%
    return SessionId
}
;
; This function switches to the desktop number provided.
;
SwitchDesktopByNumber(targetDesktop)
{
    global _CurrentDesktop, _DesktopCount
    ; Re-generate the list of desktops and where we fit in that. We do this because
    ; the user may have switched desktops via some other means than the script.
    MapDesktopsFromRegistry()
    ; Don't attempt to switch to an invalid desktop
    if (targetDesktop > _DesktopCount || targetDesktop < 1) {
        OutputDebug, [invalid] target: %targetDesktop% current: %_CurrentDesktop%
        return
    }
    ; Go right until we reach the desktop we want
    while(_CurrentDesktop < targetDesktop) {
        Send ^#{Right}
        _CurrentDesktop++
        OutputDebug, [right] target: %targetDesktop% current: %_CurrentDesktop%
    }
    ; Go left until we reach the desktop we want
    while(_CurrentDesktop > targetDesktop) {
        Send ^#{Left}
        _CurrentDesktop--
        OutputDebug, [left] target: %targetDesktop% current: %_CurrentDesktop%
    }
}
;
; This function creates a new virtual desktop and switches to it
;
CreateVirtualDesktop()
{
    global _CurrentDesktop, _DesktopCount
    Send, #^d
    _DesktopCount++
    _CurrentDesktop = %_DesktopCount%
    OutputDebug, [create] desktops: %_DesktopCount% current: %_CurrentDesktop%
}
;
; This function deletes the current virtual desktop
;
DeleteVirtualDesktop()
{
    global _CurrentDesktop, _DesktopCount
    Send, #^{F4}
    _DesktopCount--
    _CurrentDesktop--
    OutputDebug, [delete] desktops: %_DesktopCount% current: %_CurrentDesktop%
}
