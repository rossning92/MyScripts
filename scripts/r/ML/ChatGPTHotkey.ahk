#SingleInstance, Force
#include <GetSelectedText>

SendMode Input
SetWorkingDir, %A_ScriptDir%

#If not WinActive("ahk_exe vncviewer.exe")

!9::
    text := GetSelectedText()
    tempFile = %A_Temp%\text_input.txt
    FileDelete, %tempFile%
    FileAppend, %text%, %tempFile%, UTF-8
    Run, run_script r/ML/chatgpt.py --copy-to-clipboard --custom-prompts "%tempFile%"
return

!8::
    KeyWait, Alt, U
    text := GetSelectedText()
    tempFile = %A_Temp%\text_input.txt
    FileDelete, %tempFile%
    FileAppend, %text%, %tempFile%, UTF-8
    Run, run_script r/ML/langchain/summerize_doc.py "%tempFile%"
return

!7::
    KeyWait, Alt, U
    text := GetSelectedText()
    tempFile = %A_Temp%\text_input.txt
    FileDelete, %tempFile%
    FileAppend, %text%, %tempFile%, UTF-8
    Run, run_script r/ML/langchain/qa.py "%tempFile%"
return

#If