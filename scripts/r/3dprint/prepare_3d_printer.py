import os

from _shutil import write_temp_file
from ext.run_script_ssh import run_bash_script_putty

if __name__ == "__main__":
    bash = (
        'pronsole -e "connect" -e "block_until_online" -e "settemp 200" -e "bedtemp 50"'
    )
    bash_file = write_temp_file(bash, ".sh")
    run_bash_script_putty(
        bash_file,
        host=os.environ["PRINTER_3D_HOST"],
        user=os.environ["PRINTER_3D_USER"],
        pwd=os.environ["PRINTER_3D_PWD"],
    )
