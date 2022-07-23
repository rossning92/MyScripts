#SingleInstance, Force

if not WinExist("Adobe Premiere Pro")
{
    ExitApp
}
return

SetKeyDelay, 100, 100

^1:: ; Choose clip you want to extend first
    KeyWait, Control, U

    Send +{End}
    Send !c ; Clip menu
    Send v ; Video options
    Send {Down}{Enter} ; Add frame hold

    Send ^{Down} ; Next clip: frame hold clip
    Send !e ; Edit menu
    Send l ; Label
    Send m{Enter} ; Mango

    Send ^{Down} ; Next clip: the clip after
    Send +q ; Extend previous edit to playhead

return
