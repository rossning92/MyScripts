import os

from _pkgmanager import require_package
from _script import get_data_dir, run_script
from _shutil import setup_logger, start_process

if __name__ == "__main__":
    setup_logger()

    log_file = os.path.join(get_data_dir(), "MyScripts.log")
    # run_script(
    #     "/r/logviewer.sh",
    #     args=[
    #         log_file,
    #     ],
    # )
    start_process([require_package("klogg"), "--follow", log_file])
