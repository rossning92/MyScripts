' Constants
msoTrue = -1
msoFalse = 0
ppSaveAsOpenXMLTemplate = 26

Set fso = CreateObject("Scripting.FileSystemObject")
Set app = CreateObject("PowerPoint.Application")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
templateFile = scriptDir & "\MyTemplate.potx"

' Parse arguments
' shouldExportShapes = WScript.Arguments.Named.Exists("shape")
' loadFromFile = (Wscript.Arguments.Unnamed.Count = 1)
' sldIndex = WScript.Arguments.Named("i")

app.ActivePresentation.SaveCopyAs templateFile, ppSaveAsOpenXMLTemplate

' Remove all slides in template file
Set presentation = app.Presentations.Open(templateFile, msoFalse, msoFalse, msoFalse)
For i = presentation.Slides.Count To 1 Step -1
    presentation.Slides(i).Delete
Next
presentation.SaveAs templateFile, ppSaveAsOpenXMLTemplate
presentation.Close
