' Powerpoint app object
Set app = CreateObject("PowerPoint.Application")

Output = ""
For Each oSlide In app.ActiveWindow.Selection.SlideRange
    With oSlide.SlideShowTransition
        ' MsgBox .Duration
        ' MsgBox .AdvanceTime
        Output = Output & .Duration & ", " & .AdvanceTime & vbCrLf
    End With
Next

Wscript.Echo Output