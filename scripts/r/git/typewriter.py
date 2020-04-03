from _shutil import *

proj_dir = r'C:\Users\Ross\Projects\UnityToonShader'

rev = '91d6155496d3d5fb0a476ecd8903e34c46cb5e92'


def insert_line(line_no, line):
    print(line_no, line)

    exec_ahk('''
    WinActivate ahk_exe devenv.exe
    MouseClick, L, 500, 500

    Send ^g
    Send ''' + str(line_no) + '''
    Send {Enter}

    SendLevel 1
    Send ^{F6}
    SendLevel 0

    Sleep 1000

    Send {Home}
    Send ^{Enter}

    s := "''' + line + '''"
    leadingSpace := True
    Loop, Parse, s
    {
        SendRaw %A_LoopField%
        if (A_LoopField = "`t")
        {
            Sleep 30
        }
        else if (A_LoopField = " ")
        {
            if (not leadingSpace)
            {
                Sleep 300
            }
        }
        else
        {
            leadingSpace := False
            Random, t, 25, 75
            Sleep %t%
        }
    }

    Sleep 2000

    SendLevel 1
    Send ^{F6}
    SendLevel 0
    
    ''')

    time.sleep(2)
    sys.exit(0)


cd(proj_dir)

args = f'git --no-pager diff {rev}^ {rev}'
print2(args)
s = get_output(args)
lines = s.splitlines()

line_no = None
for l in lines:
    m = re.match(r'@@ -(\d+),(\d+) \+(\d+),(\d+) @@', l)
    if m:
        line_no = int(m.group(1))
    else:
        if line_no is not None:
            if l.startswith('+'):
                added_line = l[1:]
                insert_line(line_no, added_line)

            line_no += 1
