Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)

Set app = CreateObject("PowerPoint.Application")
app.Visible = True

Set presentation = app.Presentations.Add
presentation.ApplyTemplate(scriptDir & "\MyTemplate.potx")

ppLayoutBlank = 12
presentation.Slides.Add 1, ppLayoutBlank

Set objArgs = Wscript.Arguments
If objArgs.Unnamed.Count = 1 Then
    outFile = objArgs.Unnamed.Item(0)
    WScript.Echo outFile
    presentation.SaveCopyAs (outFile)
End If
