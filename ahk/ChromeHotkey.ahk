#SingleInstance, Force
#InstallKeybdHook

SetTitleMatchMode, 2

HotkeyInfo := {}
KeyWindowMap := {}

AddChromeHotkey(hotkey, title, url, open:=False)
{
    global HotkeyInfo
    HotkeyInfo[hotkey] := {"title": title, "url": url}
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
    global HotkeyInfo
    global KeyWindowMap

    chrome := GetChrome()

    title := HotkeyInfo[key].title ; Deprecated
    url := HotkeyInfo[key].url

    if (KeyWindowMap.HasKey(key))
    {
        win_id := KeyWindowMap[key]
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
        KeyWindowMap[key] := win_id
        ToolTip, %key% => %win_id%, 0, 0
        SetTimer, RemoveToolTip, -2000
    }
}

RemoveToolTip()
{
    ToolTip
    return
}
