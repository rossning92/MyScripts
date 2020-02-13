from _shutil import *

args = 'plink -ssh {{SSH_USER}}@{{SSH_HOST}}'
if '{{SSH_PWD}}':
    args += ' -pw {{SSH_PWD}}'
call2(args)
