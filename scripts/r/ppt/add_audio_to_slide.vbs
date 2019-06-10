Const msoFalse = 0
Const msoTrue = -1
Const msoAnimTriggerWithPrevious = 2

Set wshShell = CreateObject( "WScript.Shell" )
audioFile = wshShell.ExpandEnvironmentStrings( "%AUDIO_FILE%" )

' Powerpoint app object
Set app = CreateObject("PowerPoint.Application")
mWidth = app.ActivePresentation.PageSetup.SlideWidth
mHeight = app.ActivePresentation.PageSetup.SlideHeight

' Get current slide
mCurSlideIndex = app.ActiveWindow.Selection.SlideRange.SlideIndex
Set mCurSlide = app.ActivePresentation.Slides(mCurSlideIndex)

' Add audio
Set mShape = mCurSlide.Shapes.AddMediaObject2( audioFile, _
                                               msoFalse, _
                                               msoTrue, _
                                               mWidth + 10, _ 
                                               0 )
With mShape.AnimationSettings.PlaySettings
    .PlayOnEntry = True
    .PauseAnimation = False
End With

' Slide transition
mMediaLength = mShape.MediaFormat.EndPoint - mShape.MediaFormat.StartPoint
With mCurSlide.SlideShowTransition
    .AdvanceOnClick = msoFalse
    .AdvanceOnTime = msoTrue
    .AdvanceTime = mMediaLength / 1000
End With

Set mySeq = mCurSlide.TimeLine.MainSequence
Set myEffect = mySeq.FindFirstAnimationFor(mShape)
myEffect.Timing.TriggerType = msoAnimTriggerWithPrevious