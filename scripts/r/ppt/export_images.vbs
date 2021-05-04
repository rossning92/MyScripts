Set objShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
Set app = CreateObject("PowerPoint.Application")

Function PadDigits(val, digits)
    PadDigits = Right(String(digits,"0") & val, digits)
End Function

' Parse arguments
ExportShapes = WScript.Arguments.Named.Exists("shape")
LoadFromFile = (Wscript.Arguments.Unnamed.Count = 1)

If LoadFromFile Then
    ' Load presentation file
    fileName = Wscript.Arguments.Unnamed.Item(0)
    Wscript.Echo fileName
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
    ' Export all shapes as PNG
    ppShapeFormatPNG = 2
    ppRelativeToSlide = 1
    ppClipRelativeToSlide = 2
    ppScaleToFit = 3
    ppScaleXY = 4
    For Each sld In ppt.Slides
        app.ActiveWindow.View.GotoSlide (sld.SlideIndex)
        sld.Shapes.SelectAll
        Set shGroup = app.ActiveWindow.Selection.ShapeRange

        shGroup.Export exportDir & "\\" & PadDigits(sld.SlideIndex, 3) & ".png", _
                       ppShapeFormatPNG, _
                       1440, _
                       810, _
                       ppRelativeToSlide

        app.ActiveWindow.Selection.Unselect
    Next
Else
    ' Get slide parameters
    w = ppt.PageSetup.SlideWidth
    h = ppt.PageSetup.SlideHeight
    w = Int(w / h * 1080)
    h = 1080

    ' Export all slides
    For Each sld In ppt.Slides
        fileName = exportDir & "\\" & PadDigits(sld.SlideIndex, 3) & ".png"
        sld.Export fileName, "PNG", w, h
    Next
End If

If LoadFromFile Then
    ppt.Close
End If

' Open export directory in explorer
' objShell.Run("explorer.exe " & exportDir)

' app.Quit
