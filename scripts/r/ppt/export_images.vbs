Function PadDigits(val, digits)
    PadDigits = Right(String(digits,"0") & val, digits)
End Function

Set objShell = CreateObject( "WScript.Shell" )
Set fso = CreateObject("Scripting.FileSystemObject")
Set app = CreateObject("PowerPoint.Application")

exportFolder = app.ActivePresentation.Path & "\\" & fso.GetBaseName(fso.GetFile(app.ActivePresentation.FullName))
w = app.ActivePresentation.PageSetup.SlideWidth
h = app.ActivePresentation.PageSetup.SlideHeight

w = Int(w / h * 1080)
h = 1080


If NOT (fso.FolderExists(exportFolder)) Then
    fso.CreateFolder(exportFolder)
End If


i = 0
For Each sld In app.ActivePresentation.Slides
    fileName = exportFolder & "\\" & PadDigits(i, 4) & ".png"
    sld.Export fileName, "PNG", w, h
    i = i + 1
Next

objShell.Run(exportFolder)

' app.Quit
