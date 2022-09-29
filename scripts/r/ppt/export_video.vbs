Set wshShell = CreateObject( "WScript.Shell" )
Set app = CreateObject("PowerPoint.Application")
Set fso = CreateObject("Scripting.FileSystemObject")

' Parse arguments
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

outFile = ppt.Path & "\" & fso.GetBaseName(fso.GetFile(ppt.FullName)) & ".mp4"

UseTimingsAndNarrations = True
VertResolution          = 1080
FramesPerSecond         = 60
Quality                 = 100
FileName                = outFile
DefaultSlideDuration    = 4

ppt.CreateVideo _
    FileName, _
    UseTimingsAndNarrations, _
    DefaultSlideDuration, _
    VertResolution, _
    FramesPerSecond, _
    Quality

' Wait to be finished
Do While ppt.CreateVideoStatus = 1 'ppMediaTaskStatusInProgress
    WScript.Sleep 100
Loop

If LoadFromFile Then
    ppt.Close
End If
