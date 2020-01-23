from _script import *

TEMP_SHELL_SCRIPT_PATH = '/tmp/tmp_script.sh'

script = ScriptItem(os.environ['ROSS_SELECTED_SCRIPT_PATH'])
tmp_script_file = write_temp_file(script.render(), '.sh')

if script.ext != '.sh':
    print('Script type is not supported: %s' % script.ext)
    exit(0)

if sys.platform == 'win32':
    call2('plink -ssh {{SSH_USER}}@{{SSH_HOST}} -m ' + tmp_script_file)
else:
    print2('Upload shell script...')
    call2(['scp',
        tmp_script_file,  # source
        '{{SSH_USER}}@{{SSH_HOST}}:' + TEMP_SHELL_SCRIPT_PATH])  # dest

    print2('Run shell script on {{SSH_USER}}@{{SSH_HOST}}...')
    call2(['ssh', '{{SSH_USER}}@{{SSH_HOST}}', 'bash ' + TEMP_SHELL_SCRIPT_PATH])
