#SingleInstance, Force

SetWorkingDir %A_ScriptDir%


#if WinActive("ahk_exe explorer.exe") or WinActive("ahk_exe everything.exe") or WinActive("ahk_exe Nomad.exe") or WinActive("ahk_exe FreeCommander.exe") or WinActive("ahk_exe doublecmd.exe")

    F5::
        filePath := getSelectedFilePath()
		Run python _open_with.py "%filePath%"
        return
        
#if


getSelectedFilePath()
{
	; Save clipboard
    clipSaved := ClipboardAll

	; Get file path
	Clipboard =
    Send ^c
    ClipWait, 0.2
    if ErrorLevel
        return
    filePath = %clipboard%

	; Restore clipboard
    Clipboard := clipSaved
    clipSaved =
    
	; Check file existance
	if not FileExist(filePath)
		return

    ; Check if selected file is a shortcut
    SplitPath filePath, , , ext
    StringLower ext, ext
    if (ext = "lnk")
    {
        ; get target file path
        FileGetShortcut %filePath%, filePath
    }
	
    return filePath
}
