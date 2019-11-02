#SingleInstance, Force


ToolTip, F7 to start`nF12 to exit
return


F7::
	StartStopRecord()
	ToolTip
	return
	

F12::
	ExitApp
	return


StartStopRecord()
{
	if WinExist("ahk_exe ffmpeg.exe")
	{
		StopRecord()
	}
	else
	{
		StartRecord()
	}
}

StartRecord()
{
	SetWorkingDir, %A_MyDocuments%

	FormatTime, now, R, yyyyMMdd_hhmmss

	commandLine = ffmpeg -f gdigrab -framerate 60 -i desktop ScreenRecord_%now%.mkv
	Run, % commandLine,, Min
}

StopRecord()
{
    ControlSend, ahk_parent, q, ahk_exe ffmpeg.exe
	Run, %A_MyDocuments%
}