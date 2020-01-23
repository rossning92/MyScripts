from _shutil import *

args = 'putty -ssh {{SSH_USER}}@{{SSH_HOST}}'
if '{{SSH_PWD}}':
    args += ' -pw {{SSH_PWD}}'
start_process(args)
