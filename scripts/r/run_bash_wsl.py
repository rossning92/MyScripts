from _script import *
import subprocess

args = wrap_args_wt(["wsl", "bash", "-c", "cd ~ && bash"], title="bash_on_wsl", font_size=14)
subprocess.Popen(args, close_fds=True)
