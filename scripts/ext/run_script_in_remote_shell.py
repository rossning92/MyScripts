from _script import *

if __name__ == '__main__':
    script_path = os.environ['_SCRIPT_PATH']

    script = ScriptItem(script_path)
    update_script_acesss_time(script)
    
    s = script.render() + '\n'
    tmp_script_file = write_temp_file(s, '.sh')

    if script.ext != '.sh':
        print('Script type is not supported: %s' % script.ext)
        exit(0)

    s = (
        "cat > /tmp/script.sh <<'__EOF__'\n"
        + s + '\n' +
        '__EOF__\n'
        'clear\n'
        'bash /tmp/script.sh\n'
    )
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

        Send ^c
        Sleep 500

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
