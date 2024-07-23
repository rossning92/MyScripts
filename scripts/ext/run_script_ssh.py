import argparse
import os

from _script import Script, find_script, get_variable
from _shutil import write_temp_file
from utils.remoteshell import run_bash_script_ssh

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--command", type=str, default=None)
    parser.add_argument("--host", type=str, default=None)
    parser.add_argument("--user", type=str, default=None)
    parser.add_argument("--pwd", type=str, default=None)
    parser.add_argument("file", type=str, nargs="?", default=None)

    args = parser.parse_args()

    bash_commands = ""

    # ANDROID_SERIAL
    android_serial = get_variable("ANDROID_SERIAL")
    if android_serial:
        bash_commands += "export ANDROID_SERIAL=%s\n" % android_serial

    if args.command:
        bash_commands += args.command

    elif args.file:
        file = args.file

    else:
        file = os.environ["SCRIPT"]
        if not file.endswith(".sh"):
            raise Exception("Unsuppported file extension to run via ssh.")

    script_file = find_script(file)
    if script_file is None:
        raise Exception(f"Unable to locate script: {script_file}")
    script = Script(script_file)
    bash_commands += script.render()

    tmp_file = write_temp_file(bash_commands, ".sh")

    # Prerequisites: SSH_HOST, SSH_USER, SSH_PORT and SSH_PWD
    run_bash_script_ssh(tmp_file, user=args.user, host=args.host, pwd=args.pwd)
