#SingleInstance, Force

WinClose system_stats_

; MsgBox % ComObjCreate("WScript.Shell").Exec("cmd.exe /q /c dir").StdOut.ReadAll()

CustomColor = EEAA99  ; Can be any RGB color.
Gui +LastFound +AlwaysOnTop -Caption +ToolWindow +E0x20
MyText = 123123123
Gui, Color, %CustomColor%
Gui, Font, q3 s14 c00FF00, Arial
Gui, Add, Text, vMyText w400 h400
WinSet, TransColor, %CustomColor% 150 ; Make color invisible

Gui, Show, x0 y400 w400 h400 NoActivate  

objExecObject := ComObjCreate("WScript.Shell").Exec("cmd /c title system_stats_ & python system_stats_.py")
while not objExecObject.StdOut.AtEndOfStream
{
	text =
	while not objExecObject.StdOut.AtEndOfStream
	{
		line := objExecObject.StdOut.Readline()
		if (line = "")
			break
			
		text := text . line . "`n"
	}
	
	GuiControl,, MyText, % text
}

ExitApp
return


CPULoad()
{ 
    ; By SKAN, CD:22-Apr-2014 / MD:05-May-2014. Thanks to ejor, Codeproject: http://goo.gl/epYnkO
    ; http://ahkscript.org/boards/viewtopic.php?p=17166#p17166
    
    Static PIT, PKT, PUT                           
    IfEqual, PIT,, Return 0, DllCall( "GetSystemTimes", "Int64P",PIT, "Int64P",PKT, "Int64P",PUT )

    DllCall( "GetSystemTimes", "Int64P",CIT, "Int64P",CKT, "Int64P",CUT )
    IdleTime := PIT - CIT
    KernelTime := PKT - CKT
    UserTime := PUT - CUT
    SystemTime := KernelTime + UserTime 

    PIT := CIT
    PKT := CKT
    PUT := CUT 

    Return ( ( SystemTime - IdleTime ) * 100 ) // SystemTime
} 