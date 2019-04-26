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

#If WinActive("- Gmail ahk_exe chrome.exe")
    !r::
        Send *a
        Sleep 500
        Send +i
        Sleep 500
        Send *n
        return
#If

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
    
#+c::
    Run chrome.exe --user-data-dir=%USERPROFILE%\ChromeData2
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
	
!#F4::
	; Close all explorer windows
	WinGet, winList, List, ahk_class CabinetWClass
	Loop, %winList%
	{
		this_id := winList%A_Index%
		WinClose, ahk_id %this_id%
	}
	return
	