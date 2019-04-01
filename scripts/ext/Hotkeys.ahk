#SingleInstance, Force
#InstallKeybdHook
#include _ExplorerHelper.ahk
#include <ChromeHotkey>

CONSOLE_WINDOW = MyScripts - Console
GUI_WINDOW = MyScripts - GUI

SetTitleMatchMode, 2

AddChromeHotkey("#!l", "- Wunderlist", "https://www.wunderlist.com/webapp#/lists/inbox")
AddChromeHotkey("#!m", "- Gmail", "https://mail.google.com/mail/u/0/#inbox")

return

^q::
	; If explorer is active, copy file path to clipboard
	WriteExplorerInfoToJson()

	; Activate script window
    if WinExist(CONSOLE_WINDOW) {
        WinActivate % CONSOLE_WINDOW
        WinActivate % GUI_WINDOW
    } else {
        WinActivate % GUI_WINDOW
    }
	return
	
#c::
	if WinExist("- Google Chrome ahk_exe chrome.exe") {
		WinActivate
	} else {
		Run chrome.exe
	}
	return

#If WinActive("ahk_exe ConEmu64.exe")
    Esc::
        WinClose ahk_exe ConEmu64.exe
        return
#If

~LButton & WheelUp::
    Suspend, Permit
    SoundSet +5
    SoundPlay *16
    return

~LButton & WheelDown::
    Suspend, Permit
    SoundSet -5
    SoundPlay *16
    return

#F4::
    Suspend, Permit
    WinGet, pid, PID, A
    Process, Close, %pid%
    SoundPlay %BEEP_FILE%
    return