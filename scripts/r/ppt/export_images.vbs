Function PadDigits(val, digits)
  PadDigits = Right(String(digits,"0") & val, digits)
End Function



Set wshShell = CreateObject( "WScript.Shell" )
USERPROFILE = wshShell.ExpandEnvironmentStrings( "%USERPROFILE%" )
Set wshShell = Nothing


Set app = CreateObject("PowerPoint.Application")

i = 0
For Each sld In app.ActivePresentation.Slides

	FileName = PadDigits(i, 4) & ".png"
	sld.Export FileName, "PNG", 1920, 1080
	i = i + 1

Next

' app.Quit