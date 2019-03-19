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
	
	title := hotkeyInfo[A_ThisHotkey].title
	url := hotkeyInfo[A_ThisHotkey].url
	if WinExist(title . " ahk_exe chrome.exe")
    {
        WinActivate, %title%
    }
    else
    {
        Run %chrome% --start-maximized --app=%url%
    }
}