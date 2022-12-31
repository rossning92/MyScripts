(Add-Type '[DllImport("user32.dll")]public static extern int PostMessage(int h,int m,int w,int l);' -Name a -Pas)::PostMessage(-1,0x0112,0xF170,2)
