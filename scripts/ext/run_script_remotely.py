from _script import *

TEMP_SHELL_SCRIPT_PATH = '/tmp/tmp_script.sh'
USER_HOST = '{{SSH_USER}}@{{SSH_HOST}}'

script_path = os.environ['ROSS_SELECTED_SCRIPT_PATH']
if script_path.endswith('run_script_remotely.py'):
    print('Parameter saved...')
    exit(0)

script = ScriptItem(script_path)
tmp_script_file = write_temp_file(script.render(), '.sh')

if script.ext != '.sh':
    print('Script type is not supported: %s' % script.ext)
    exit(0)

if sys.platform == 'win32':
    args = f'putty -batch -ssh {USER_HOST} -m {tmp_script_file}'
    if '{{SSH_PWD}}':
        args += ' -pw {{SSH_PWD}}'
    call2(args)
else:
    print2('Upload shell script...')
    call2(['scp',
           tmp_script_file,  # source
           USER_HOST + ':' + TEMP_SHELL_SCRIPT_PATH])  # dest

    print2(f'Run shell script on {USER_HOST}...')
    call2(['ssh', USER_HOST,
           'bash ' + TEMP_SHELL_SCRIPT_PATH])
