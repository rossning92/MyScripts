from _shutil import *

cd(r"{{TENSORBOARD_PATH}}")


call_echo(
    [
        "tensorboard",
        "--logdir=runs",
        "--samples_per_plugin=text=100"
    ]
)

