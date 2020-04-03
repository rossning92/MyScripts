from _shutil import *

if '{{_USE_GUI}}':
    prepend_to_path([
        r'C:\Program Files (x86)\Meld',
        r'C:\Program Files (x86)\Meld\lib'
    ])

    call('git config --global diff.tool meld')
    call('git config --global difftool.prompt false')
    call(['git', 'config', '--global', 'difftool.meld.cmd', 'meld "$LOCAL" "$REMOTE"'])

chdir(r'{{GIT_REPO}}')


args = 'git difftool' if '{{_USE_GUI}}' else 'git --no-pager diff'


if '{{GIT_DIFF_PREVIOUS}}':
    args += ' HEAD~{{GIT_DIFF_PREVIOUS}}'

call(args)
