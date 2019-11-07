#SingleInstance, Force
#InstallKeybdHook
#include <ExplorerHelper>
#include <ChromeHotkey>

CONSOLE_WINDOW = MyScripts - Console
GUI_WINDOW = MyScripts - GUI

SetTitleMatchMode, 2

AddChromeHotkey("#!.", "- Wunderlist", "https://www.wunderlist.com/webapp#/lists/inbox")
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

#If WinActive("ahk_exe ConEmu64.exe")
    Esc::
        WinClose ahk_exe ConEmu64.exe
        return
#If


#If not WinActive("ahk_exe vncviewer.exe") and not WinActive("ahk_exe League of Legends.exe")
	
	!a::Run "C:\Program Files\Everything\Everything.exe" -toggle-window
	#c::ActivateChrome(0)
	#!c::ActivateChrome(1)
	
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

		; Close "(Finished)" windows
		WinGet, winList, List, (Finished)
		Loop, %winList%
		{
			this_id := winList%A_Index%
			WinClose, ahk_id %this_id%
		}
		return
	
#If




ActivateChrome(index=0)
{
	if (index = 0)
	{
		condition := "NOT CommandLine LIKE '%--user-data-dir=%' AND NOT CommandLine LIKE '%--type=%'"
	}
	else
	{
		condition := "CommandLine LIKE '%ChromeData2%' AND NOT CommandLine LIKE '%--type=%'"
	}

	pid =
	for process in ComObjGet("winmgmts:").ExecQuery("SELECT * FROM Win32_Process WHERE Name='chrome.exe' AND " condition)
	{
		pid := process.ProcessID
		break
	}

	if ( pid != "" and WinExist("- Google Chrome ahk_pid " pid) )
	{
		WinActivate
	}
	else
	{
		if (index = 0)
		{
			Run chrome.exe
		}
		else
		{
			Run chrome.exe --user-data-dir=%USERPROFILE%\ChromeData2
		}
	}
}

+F1::
	Send {F1}
	WinWaitActive ahk_exe Snipaste.exe
	Send r
	Send ^+s

#v::
	WinActivate ahk_exe code.exe
	return