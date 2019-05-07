Set objShell = CreateObject("Shell.Application")

' Combine all the arguments
ReDim args(WScript.Arguments.Count-1)
For i = 1 To WScript.Arguments.Count-1
  If InStr(WScript.Arguments(i), " ") > 0 Then
    args(i) = Chr(34) & WScript.Arguments(i) & Chr(34)
  Else
    args(i) = WScript.Arguments(i)
  End If
Next

' Run command
objShell.ShellExecute WScript.Arguments(0), Join(args, " "), "", "runas", 1