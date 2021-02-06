SetTitleMatchMode, 2
SetKeyDelay, 50
TITLE = - Microsoft Visual Studio

file_path = %1%
line_no = %2%


WinActivate, %TITLE%
WinWaitActive, %TITLE%,, 3
if ErrorLevel
{
    MsgBox No Visual Studio window found.
    return
}


Send ^o
WinWaitActive, Open File,, 2
if ErrorLevel
{
    MsgBox Cannot find Open File window
    return
}
SendInput %file_path%
Send {Enter}


WinWaitActive, %TITLE%,, 2
if ErrorLevel
{
    MsgBox No Visual Studio window found.
    return
}


Send ^g
WinWaitActive, Go To Line,, 2
if ErrorLevel
{
    MsgBox Cannot find Go To Line window
    return
}
SendInput %line_no%
Send {Enter}


return



; ControlSend,, {Control Down}{Alt Down}a{Alt Up}{Control Up}, %TITLE%
; Sleep 100
; Clipboard = File.OpenFile "%file_path%"
; Send ^v
; Send {Enter}
; 
; Sleep 2000
; 
; ControlSend,, {Control Down}{Alt Down}a{Alt Up}{Control Up}, %TITLE%
; Sleep 100
; Clipboard = Edit.GoTo %line_no%
; Send ^v
; Send {Enter}
; 
; Send {Escape}
