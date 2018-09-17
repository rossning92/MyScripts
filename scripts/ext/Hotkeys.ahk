#SingleInstance, Force

CONSOLE_WINDOW = MyScripts - Console
GUI_WINDOW = MyScripts - GUI

^q::
	; If explorer is active, copy file path to clipboard
	if (WinActive("ahk_exe explorer.exe") or WinActive("ahk_exe everything.exe")) {
		Send ^c
	}

	; Activate script window
    if WinExist(CONSOLE_WINDOW) {
        WinActivate % CONSOLE_WINDOW
        WinActivate % GUI_WINDOW
    } else {
        WinActivate % GUI_WINDOW
    }
	return