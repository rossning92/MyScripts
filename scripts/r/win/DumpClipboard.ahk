#SingleInstance, Force
#Persistent
Return

OnClipboardChange:
    FileAppend, %Clipboard%`n, %A_Desktop%\Clipboard.txt
return
