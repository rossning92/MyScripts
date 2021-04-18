#SingleInstance, Force

Gui, OverlayGui:new
Gui, Margin, 0, 0
Gui, -Border -SysMenu +Owner -Caption +ToolWindow
Gui, Add, Picture,, %A_ScriptDir%\overlay.png
Gui, Show, x0 y0, OverlayWindow
return

OverlayGuiGuiEscape:
    Gui, OverlayGui:Destroy
return
