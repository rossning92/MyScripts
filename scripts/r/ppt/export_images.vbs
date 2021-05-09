Set objShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
Set app = CreateObject("PowerPoint.Application")

Function PadDigits(val, digits)
    PadDigits = Right(String(digits,"0") & val, digits)
End Function

Function ExportAsPNG(app, ppt, sld)
    ' Export all shapes as PNG
    ppShapeFormatPNG = 2
    ppRelativeToSlide = 1
    ppClipRelativeToSlide = 2
    ppScaleToFit = 3
    ppScaleXY = 4

    ppViewNormal = 9

    ppt.Windows(1).View.GotoSlide(sld.SlideIndex)
    sld.Shapes.SelectAll
    Set shGroup = ppt.Windows(1).Selection.ShapeRange

    shGroup.Export exportDir & "\\" & PadDigits(sld.SlideIndex, 3) & ".png", _
                    ppShapeFormatPNG, _
                    1440, _
                    810, _
                    ppRelativeToSlide

    ppt.Windows(1).Selection.Unselect
End Function

Function ExportSlide(ppt, sld)
    ' Get slide parameters
    w = ppt.PageSetup.SlideWidth
    h = ppt.PageSetup.SlideHeight
    w = Int(w / h * 1080)
    h = 1080

    fileName = exportDir & "\\" & PadDigits(sld.SlideIndex, 3) & ".png"
    sld.Export fileName, "PNG", w, h
End Function

' Parse arguments
ExportShapes = WScript.Arguments.Named.Exists("shape")
LoadFromFile = (Wscript.Arguments.Unnamed.Count = 1)
sldIndex = WScript.Arguments.Named.Item("i")

If LoadFromFile Then
    ' Load presentation file
    fileName = Wscript.Arguments.Unnamed.Item(0)
    Wscript.Echo "Exporting" & fileName
    Set ppt = app.Presentations.Open(fileName, True, , False)
Else
    ' Active presentation
    Set ppt = app.ActivePresentation
End If

' Get export dir
exportDir = ppt.Path & "\" & fso.GetBaseName(fso.GetFile(ppt.FullName))
If NOT (fso.FolderExists(exportDir)) Then
    fso.CreateFolder(exportDir)
End If

If ExportShapes Then
    If sldIndex <> "" Then ' Export single slide
        ExportAsPNG app, ppt, ppt.Slides(CInt(sldIndex) + 1)
    Else ' Export all slides
        For Each sld In ppt.Slides
            ExportAsPNG app, ppt, sld
        Next
    End If  
Else
    If sldIndex <> "" Then ' Export single slide
        ExportSlide ppt, ppt.Slides(CInt(sldIndex) + 1)
    Else ' Export all slides
        For Each sld In ppt.Slides
            ExportSlide ppt, sld
        Next
    End If
End If

If LoadFromFile Then
    ppt.Close
End If

' Open export directory in explorer
' objShell.Run("explorer.exe " & exportDir)

' app.Quit
