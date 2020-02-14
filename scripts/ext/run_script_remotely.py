from _script import *

TEMP_SHELL_SCRIPT_PATH = '/tmp/tmp_script.sh'
USER_HOST = '{{SSH_USER}}@{{SSH_HOST}}'


def run_bash_script_ssh(bash_script_file, user_host):
    if True:  # plink is preferred (better automation)
        args = f'plink -ssh {user_host} -m {bash_script_file}'
        if '{{SSH_PWD}}':
            args += ' -pw {{SSH_PWD}}'
        call2(args)
    else:
        print2('Upload shell script...')
        call2(['scp',
               bash_script_file,  # source
               user_host + ':' + TEMP_SHELL_SCRIPT_PATH])  # dest

        print2(f'Run shell script on {user_host}...')
        call2(['ssh', user_host,
               'bash ' + TEMP_SHELL_SCRIPT_PATH])


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
    tmp_script_file = write_temp_file(script.render(), '.sh')

    if script.ext != '.sh':
        print('Script type is not supported: %s' % script.ext)
        exit(0)

    if '{{VAGRANT_ID}}':
        run_bash_script_vagrant(tmp_script_file, '{{VAGRANT_ID}}')
    else:
        run_bash_script_ssh(tmp_script_file, USER_HOST)
