import os

from _shutil import get_files, write_temp_file

from r.linux.ssh_push import push_file
from ext.run_script_ssh import run_bash_script_plink

if __name__ == "__main__":
    file = get_files()[0]

    push_file(file)
    dst = os.path.basename(file)

    bash = (
        'pronsole -e "connect" -e "block_until_online" -e "gettemp" -e "load %s" -e "print"'
        % dst
    )
    bash_file = write_temp_file(bash, ".sh")
    run_bash_script_plink(bash_file)
