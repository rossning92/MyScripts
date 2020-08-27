Function PadDigits(val, digits)
    PadDigits = Right(String(digits,"0") & val, digits)
End Function

Set objShell = CreateObject( "WScript.Shell" )
Set fso = CreateObject("Scripting.FileSystemObject")
Set app = CreateObject("PowerPoint.Application")

exportDir = app.ActivePresentation.Path & "\" & fso.GetBaseName(fso.GetFile(app.ActivePresentation.FullName))
w = app.ActivePresentation.PageSetup.SlideWidth
h = app.ActivePresentation.PageSetup.SlideHeight

w = Int(w / h * 1080)
h = 1080


If NOT (fso.FolderExists(exportDir)) Then
    fso.CreateFolder(exportDir)
End If


i = 1
For Each sld In app.ActivePresentation.Slides
    fileName = exportDir & "\\" & PadDigits(i, 4) & ".png"
    sld.Export fileName, "PNG", w, h
    i = i + 1
Next

' Open export directory in explorer
objShell.Run("explorer.exe " & exportDir)

' app.Quit
