
Function PadDigits(val, digits)
    PadDigits = Right(String(digits,"0") & val, digits)
End Function

Set objShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
Set app = CreateObject("PowerPoint.Application")

' Load presentation file or choose active presentation
If (Wscript.Arguments.Length = 1) Then
    Wscript.Echo Wscript.Arguments(0)
    Set ppt = app.Presentations.Open(Wscript.Arguments(0), True, , False)
Else
    Set ppt = app.ActivePresentation
End If

' Get export dir
exportDir = ppt.Path & "\" & fso.GetBaseName(fso.GetFile(ppt.FullName))
If NOT (fso.FolderExists(exportDir)) Then
    fso.CreateFolder(exportDir)
End If

' Get slide parameters
w = ppt.PageSetup.SlideWidth
h = ppt.PageSetup.SlideHeight
w = Int(w / h * 1080)
h = 1080

' Export all slides
i = 1
For Each sld In ppt.Slides
    fileName = exportDir & "\\" & PadDigits(i, 4) & ".png"
    sld.Export fileName, "PNG", w, h
    i = i + 1
Next

' Open export directory in explorer
' objShell.Run("explorer.exe " & exportDir)

' app.Quit
