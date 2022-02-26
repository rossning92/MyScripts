import os

from _appmanager import get_executable
from _script import get_data_dir, run_script
from _shutil import start_process, setup_logger


if __name__ == "__main__":
    setup_logger()

    log_file = os.path.join(get_data_dir(), "MyScripts.log")
    run_script(
        "/r/logviewer.sh",
        args=[
            log_file,
        ],
    )
    # start_process([get_executable("klogg"), "--follow", log_file])
