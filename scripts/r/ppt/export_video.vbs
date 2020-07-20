Set wshShell = CreateObject( "WScript.Shell" )
Set app = CreateObject("PowerPoint.Application")
Set fso = CreateObject("Scripting.FileSystemObject")

' USERPROFILE = wshShell.ExpandEnvironmentStrings( "%USERPROFILE%" )

outFile = app.ActivePresentation.Path & "\" & fso.GetBaseName(fso.GetFile(app.ActivePresentation.FullName)) & ".mp4"

UseTimingsAndNarrations = True
VertResolution          = 1080
FramesPerSecond         = 60
Quality                 = 100
FileName                = outFile
DefaultSlideDuration    = 4

app.ActivePresentation.CreateVideo _
    FileName, _
    UseTimingsAndNarrations, _
    DefaultSlideDuration, _
    VertResolution, _
    FramesPerSecond, _
    Quality

' app.Quit