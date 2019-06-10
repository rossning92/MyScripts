Set wshShell = CreateObject( "WScript.Shell" )
USERPROFILE = wshShell.ExpandEnvironmentStrings( "%USERPROFILE%" )
Set wshShell = Nothing


Set objPPT = CreateObject("PowerPoint.Application")

UseTimingsAndNarrations = True
VertResolution          = 1080
FramesPerSecond         = 60
Quality                 = 100
FileName                = USERPROFILE & "\Desktop\Your PowerPoint Video.wmv"
DefaultSlideDuration    = 4

objPPT.ActivePresentation.CreateVideo _
    FileName, _
    UseTimingsAndNarrations, _
    DefaultSlideDuration, _
    VertResolution, _
    FramesPerSecond, _
    Quality

' objPPT.Quit