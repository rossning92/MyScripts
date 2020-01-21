from _script import *

TEMP_SHELL_SCRIPT_PATH = '/tmp/tmp_script.sh'

script = ScriptItem(os.environ['ROSS_SELECTED_SCRIPT_PATH'])

if script.ext != '.sh':
    print('Script type is not supported: %s' % script.ext)
    exit(0)

print2('Upload shell script...')
tmp_script_file = write_temp_file(script.render(), '.sh')
call2(['scp',
       tmp_script_file,  # source
       '{{SSH_USER}}@{{SSH_HOST}}:' + TEMP_SHELL_SCRIPT_PATH])  # dest

print2('Run shell script on {{SSH_USER}}@{{SSH_HOST}}...')
call2(['ssh', '{{SSH_USER}}@{{SSH_HOST}}', 'bash ' + TEMP_SHELL_SCRIPT_PATH])
