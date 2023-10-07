import glob
import os

from _script import get_my_script_root
from find_in_files import find_in_files

if __name__ == "__main__":
    find_in_files(
        files=(
            file
            for file in glob.glob(
                os.path.join(get_my_script_root(), "**", "*"), recursive=True
            )
            if os.path.isfile(file) and "node_modules" not in file
        ),
        history_file=os.path.join(
            os.environ["MY_DATA_DIR"], "find_in_myscripts_config.json"
        ),
    )
