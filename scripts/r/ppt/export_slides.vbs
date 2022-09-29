' Constants
msoTrue = -1
msoFalse = 0
ppShapeFormatPNG = 2
ppRelativeToSlide = 1
ppClipRelativeToSlide = 2
ppScaleToFit = 3
ppScaleXY = 4
ppViewNormal = 9

Set fso = CreateObject("Scripting.FileSystemObject")
Set app = CreateObject("PowerPoint.Application")

Function PadDigits(val, digits)
    PadDigits = Right(String(digits,"0") & val, digits)
End Function

Function ExportShapes(sld)
    ' Export all shapes as PNG
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

Function ExportSlide(sld)
    ' Get slide parameters
    w = ppt.PageSetup.SlideWidth
    h = ppt.PageSetup.SlideHeight
    w = Int(w / h * 1080)
    h = 1080

    fileName = exportDir & "\\" & PadDigits(sld.SlideIndex, 3) & ".png"
    sld.Export fileName, "PNG", w, h
End Function

' Parse arguments
shouldExportShapes = WScript.Arguments.Named.Exists("shape")
loadFromFile = (Wscript.Arguments.Unnamed.Count = 1)
sldIndex = WScript.Arguments.Named("i")

If loadFromFile Then
    ' Load presentation file
    fileName = Wscript.Arguments.Unnamed(0)
    Wscript.Echo "Exporting " & fileName

    If shouldExportShapes Then
        ww = msoTrue ' WithWindow
    Else
        ww = msoFalse
    End If
    Set ppt = app.Presentations.Open(fileName, msoTrue, , ww)
Else
    ' Active presentation
    Set ppt = app.ActivePresentation
End If

' Get export dir
exportDir = ppt.Path & "\" & fso.GetBaseName(fso.GetFile(ppt.FullName))
If NOT (fso.FolderExists(exportDir)) Then
    fso.CreateFolder(exportDir)
End If

If shouldExportShapes Then
    If sldIndex <> "" Then ' Export single slide
        ExportShapes ppt.Slides(CInt(sldIndex))
    Else ' Export all slides
        For Each sld In ppt.Slides
            ExportShapes sld
        Next
    End If
Else
    If sldIndex <> "" Then ' Export single slide
        ExportSlide ppt.Slides(CInt(sldIndex))
    Else ' Export all slides
        For Each sld In ppt.Slides
            ExportSlide sld
        Next
    End If
End If

If loadFromFile Then
    ppt.Close
End If
