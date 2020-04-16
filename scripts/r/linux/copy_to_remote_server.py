from _shutil import *


call_echo(
    [
        "pscp",
        "-pw",
        "{{SSH_PWD}}",
        "-P",
        "1234",
        get_files()[0],
        "{{SSH_USER}}@localhost:/home/{{SSH_USER}}",
    ]
)

