#SingleInstance, Force
#InstallKeybdHook

SetTitleMatchMode, 2

hotkeyInfo := {}

AddChromeHotkey(hotkey, title, url, open:=False)
{
	global hotkeyInfo
	hotkeyInfo[hotkey] := {"title": title, "url": url}
	Hotkey, %hotkey%, HotkeyPressed

    if (open)
    {
        ActivateChromeWindow(hotkey)
    }
}

HotkeyPressed()
{
    ActivateChromeWindow(A_ThisHotkey)
}

GetChrome() {
    chrome := "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    if not FileExist(chrome)
    {
        chrome := "C:\Program Files\Google\Chrome\Application\chrome.exe"
    }
    return chrome
}

ActivateChromeWindow(key)
{
    global hotkeyInfo
    chrome := GetChrome()

    title := hotkeyInfo[key].title  ; Deprecated
	url := hotkeyInfo[key].url

    RegRead, win_id, HKEY_CURRENT_USER\Software\ChromeHotkey, %key%
    if WinExist("ahk_id" win_id)
    {
        WinActivate ahk_id %win_id%
    }
    else
    {
        WinGet, current_win_id, ID, A
        Run %chrome% --start-maximized --app=%url%
        WinWaitNotActive, ahk_id %current_win_id%

        WinWaitActive, ahk_exe chrome.exe,, 10
        if ErrorLevel
        {
            SoundPlay *16
            return
        }

        WinGet, win_id, ID
        RegWrite, REG_SZ, HKEY_CURRENT_USER, Software\ChromeHotkey, %key%, %win_id%
        ToolTip, %key% => %win_id%, 0, 0
        SetTimer, RemoveToolTip, -2000
    }
}

RemoveToolTip()
{
    ToolTip
    return
}
