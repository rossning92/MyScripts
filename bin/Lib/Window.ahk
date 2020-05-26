LayoutWindows(title)
{
	WinGet, winList, List, %title%
	n := winList
	
	rows := Floor(Sqrt(n))
	cols := n // rows
	
	if ( mod(n, rows) > 0 )
		cols := cols + 1
	
	t := rows
	rows := cols
	cols := t
	
	SysGet, workArea, MonitorWorkArea
	width := (workAreaRight - workAreaLeft) // cols
	height := (workAreaBottom - workAreaTop) // rows
	
	Loop, %winList%
	{
		this_id := winList%A_Index%
		
		i := (A_Index - 1) // cols
		j := mod(A_Index - 1, cols)
		
		x := workAreaLeft + j * width
		y := workAreaTop + i * height
		
		; Msgbox %x%|%y%|%width%|%height%
		
		WinRestore, ahk_id %this_id%
		WinActivate, ahk_id %this_id%
		WinMove ahk_id %this_id%,, %x%, %y%, %width%, %height%
	}
}


CloseWindows(title)
{
	WinGet, winList, List, %title%
	Loop, %winList%
	{
		this_id := winList%A_Index%
		WinClose, ahk_id %this_id%
	}
}