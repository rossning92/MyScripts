#SingleInstance, Force
#InstallKeybdHook

SetTitleMatchMode, 2

hotkeyInfo := {}
hotkeyHwndMap := {}

AddChromeHotkey(hotkey, title, url)
{
	global hotkeyInfo
	hotkeyInfo[hotkey] := {"title": title, "url": url}
	Hotkey, %hotkey%, HotkeyPressed
}

HotkeyPressed()
{
	global hotkeyInfo
    global hotkeyHwndMap
	
	chrome = "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
	
	title := hotkeyInfo[A_ThisHotkey].title
	url := hotkeyInfo[A_ThisHotkey].url
	if WinExist(title . " ahk_exe chrome.exe")
    {
        WinActivate
        WinGet, hwnd, ID
        hotkeyHwndMap[A_ThisHotkey] := hwnd
    }
    else if ( hotkeyHwndMap.HasKey(A_ThisHotkey) and WinExist("ahk_id" hotkeyHwndMap[A_ThisHotkey]) )
    {
        WinActivate % hotkeyHwndMap[A_ThisHotkey]
    }
    else
    {
        Run %chrome% --start-maximized --app=%url%
    }
}
