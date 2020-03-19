from _script import *

TEMP_SHELL_SCRIPT_PATH = '/tmp/tmp_script.sh'


def run_bash_script_ssh(bash_script_file, user_host, ssh_port=None, ssh_pwd=None):
    if 1:  # plink is preferred (better automation)
        # -t switch to force a use of an interactive session
        args = f'plink -ssh -t {user_host} -m {bash_script_file}'
        if ssh_pwd:
            args += ' -pw %s' % ssh_pwd
        if ssh_port:
            args += ' -P %d' % ssh_port
        call_echo(args)

    else:
        # print2('Upload shell script...')
        call2(['scp',
               bash_script_file,  # source
               user_host + ':' + TEMP_SHELL_SCRIPT_PATH])  # dest

        print2(f'Run shell script on {user_host}...')
        args = ['ssh', user_host]
        if ssh_port:
            args += ['-p', '%d' % ssh_port]

        args += [TEMP_SHELL_SCRIPT_PATH]
        call2(args)


def run_bash_script_vagrant(bash_script_file, vagrant_id):
    call2(
        f'vagrant upload {bash_script_file} {TEMP_SHELL_SCRIPT_PATH} {vagrant_id}')
    call2(f'vagrant ssh -c "bash {TEMP_SHELL_SCRIPT_PATH}" {vagrant_id}')


if __name__ == '__main__':
    script_path = os.environ['ROSS_SELECTED_SCRIPT_PATH']
    if script_path.endswith('run_script_remotely.py'):
        print('Parameter saved...')
        exit(0)

    script = ScriptItem(script_path)
    update_script_acesss_time(script)
    tmp_script_file = write_temp_file(script.render(), '.sh')

    if script.ext != '.sh':
        print('Script type is not supported: %s' % script.ext)
        exit(0)

    if '{{VAGRANT_ID}}':
        run_bash_script_vagrant(tmp_script_file, '{{VAGRANT_ID}}')
    else:
        ssh_host = '{{SSH_USER}}@{{SSH_HOST}}'
        ssh_port = int('{{SSH_PORT}}') if '{{SSH_PORT}}' else None
        ssh_pwd = r'{{SSH_PWD}}' if r'{{SSH_PWD}}' else None
        run_bash_script_ssh(tmp_script_file,
                            ssh_host,
                            ssh_port,
                            ssh_pwd=ssh_pwd)
