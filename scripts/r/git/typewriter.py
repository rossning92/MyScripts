from _shutil import *
from _term import *

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

Send {Up}
Send {End}

s := "''' + line.replace('"', '""').replace('\n', '`n') + '''"

Loop, parse, s, `n, `r
{
    Send {Enter}
    Sleep 200

    leadingSpace := True
    Loop, Parse, A_LoopField
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
}

Sleep 2000

SendLevel 1
Send ^{F6}
SendLevel 0
    ''')

    time.sleep(2)


cd(proj_dir)


lines = list(proc_lines('git log --pretty="format:%h %s" master'))
i = 2
i = prompt_list(lines)

commit, message = lines[i].split(maxsplit=1)

# call_echo(['git', 'checkout', commit + '^'], shell=False)

args = f'git --no-pager diff {commit}^ {commit}'
s = get_output(args)
lines = s.splitlines()


line_no = None
line_start = None
content = []
i = 0
for line in lines:
    m = re.match(r'@@ -(\d+),(\d+) \+(\d+),(\d+) @@', line)
    if m:
        line_no = int(m.group(3))
    else:
        if line_no is not None:
            if line.startswith('+'):

                if line_start is None:
                    line_start = line_no

                content.append(line[1:])

            elif line_start is not None:
                if i == 0:
                    insert_line(line_start, '\n'.join(content))

                line_start = None
                content.clear()
                i += 1

            line_no += 1
