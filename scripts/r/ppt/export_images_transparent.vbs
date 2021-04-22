
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

' Export all slides
ppShapeFormatPNG = 2
ppRelativeToSlide = 1
For Each slide_ In ppt.Slides
    app.ActiveWindow.View.GotoSlide (slide_.SlideIndex)
    slide_.Shapes.SelectAll
    Set shGroup = app.ActiveWindow.Selection.ShapeRange
    shGroup.Export exportDir & "\\" & PadDigits(slide_.SlideIndex, 3) & ".png", _
                        ppShapeFormatPNG, , , ppRelativeToSlide
Next
