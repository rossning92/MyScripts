from _shutil import *

if '{{_DST_DIR}}':
    dst = '{{_DST_DIR}}'
else:
    dst = '/home/{{SSH_USER}}'

call_echo(
    [
        "pscp",
        "-pw",
        "{{SSH_PWD}}",
        get_files()[0],
        "{{SSH_USER}}@{{SSH_HOST}}:" + dst,
    ]
)

