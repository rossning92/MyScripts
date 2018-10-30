#SingleInstance, Force
#include _ExplorerHelper.ahk


CONSOLE_WINDOW = MyScripts - Console
GUI_WINDOW = MyScripts - GUI


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
	if WinExist("ahk_exe chrome.exe") {
		WinActivate
	} else {
		Run chrome.exe
	}
	return
