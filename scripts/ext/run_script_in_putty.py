from _script import *

if __name__ == '__main__':
    script_path = os.environ['ROSS_SELECTED_SCRIPT_PATH']

    script = ScriptItem(script_path)
    s = script.render() + '\n'
    tmp_script_file = write_temp_file(s, '.sh')

    if script.ext != '.sh':
        print('Script type is not supported: %s' % script.ext)
        exit(0)

    set_clip(s)
    # exec_ahk('''
    #     WinActivate ahk_exe putty.exe
    #     WinWaitActive ahk_exe putty.exe
    #     if ErrorLevel
    #         return

    #     Send +{Ins}
    # ''')

    exec_ahk('''
        WinActivate r/linux/et
        WinWaitActive r/linux/et,, 2
        if ErrorLevel
            return

        Send ^v

        ; Loop 2 {
        ;    WinWaitActive, ahk_exe ConEmu64.exe, Continue?, 2
        ;    if ErrorLevel
        ;        return
        ;    Send {Enter}
        ; }

        ; Execute the last line
        ; Send {Enter}
    ''')
