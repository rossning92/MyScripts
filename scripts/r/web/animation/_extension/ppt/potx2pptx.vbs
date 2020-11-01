Set objArgs = Wscript.Arguments
outFile = Wscript.Arguments(0)
WScript.Echo outFile

Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)

Set objPPT = CreateObject("PowerPoint.Application")
objPPT.Visible = True

Set objPresentation = objPPT.Presentations.Add
objPresentation.ApplyTemplate(scriptDir & "\dark-template.potx")
objPresentation.SaveAs(outFile)
