#SingleInstance, Force
#InstallKeybdHook

SetTitleMatchMode, 2

hotkeyInfo := {}

AddChromeHotkey(hotkey, title, url)
{
	global hotkeyInfo
	hotkeyInfo[hotkey] := {"title": title, "url": url}
	Hotkey, %hotkey%, HotkeyPressed
}

HotkeyPressed()
{
	global hotkeyInfo

	chrome = "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"

	title := hotkeyInfo[A_ThisHotkey].title  ; Deprecated
	url := hotkeyInfo[A_ThisHotkey].url

    RegRead, win_id, HKEY_CURRENT_USER\Software\ChromeHotkey, %A_ThisHotkey%
    if WinExist("ahk_id" win_id)
    {
        WinActivate ahk_id %win_id%
    }
    else
    {
        WinGet, current_win_id, ID, A
        Run %chrome% --start-maximized --app=%url%
        WinWaitNotActive, ahk_id %current_win_id%
        WinWait, ahk_exe chrome.exe,, 10
        if ErrorLevel
        {
            SoundPlay *16
            return
        }

        WinGet, win_id, ID
        RegWrite, REG_SZ, HKEY_CURRENT_USER, Software\ChromeHotkey, %A_ThisHotkey%, %win_id%
        ToolTip, Chrome detected, 0, 0
        SetTimer, RemoveToolTip, -2000
    }
}

RemoveToolTip()
{
    ToolTip
    return
}
