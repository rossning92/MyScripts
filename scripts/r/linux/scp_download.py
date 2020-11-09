from _shutil import *

if '{{_SRC}}':
    src = '{{_SRC}}'
else:
    src = '/home/{{SSH_USER}}'

call_echo(
    [
        "pscp",
        "-pw",
        "{{SSH_PWD}}",
        "{{SSH_USER}}@{{SSH_HOST}}:" + src,
        os.environ['_CUR_DIR'],
    ]
)

