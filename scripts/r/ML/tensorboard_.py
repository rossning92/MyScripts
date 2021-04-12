from _shutil import *

cd(r"{{TENSORBOARD_PATH}}")


call_echo(["tensorboard", "--logdir=runs"])

