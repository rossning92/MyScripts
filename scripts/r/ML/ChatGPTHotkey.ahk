#SingleInstance, Force
SendMode Input
SetWorkingDir, %A_ScriptDir%

GetSelectedText() {
    clipSaved := ClipboardAll

    Clipboard =
    Send ^c
    ClipWait, 0.2
    if ErrorLevel {
        Clipboard := clipSaved
        return
    }

    return Clipboard
}

!9::
    text := GetSelectedText()
    temp_file = %A_Temp%\chatgpt_text_input.txt
    FileDelete, %temp_file%
    FileAppend, %text%, %temp_file%
    Run, run_script r/ML/chatgpt.py --copy-to-clipboard --custom-prompts "%temp_file%"
