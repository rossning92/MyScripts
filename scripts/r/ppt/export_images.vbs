Set wshShell = CreateObject( "WScript.Shell" )
USERPROFILE = wshShell.ExpandEnvironmentStrings( "%USERPROFILE%" )
Set wshShell = Nothing


Set app = CreateObject("PowerPoint.Application")

FileName                = USERPROFILE & "\Desktop\Slide.png"

For Each sld In app.ActivePresentation.Slides

	sld.Export FileName, "PNG", 1920, 1080

Next

' app.Quit