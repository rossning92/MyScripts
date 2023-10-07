import os

from _script import get_all_scripts
from find_in_files import find_in_files

if __name__ == "__main__":
    find_in_files(
        files=get_all_scripts(),
        history_file=os.path.join(
            os.environ["MY_DATA_DIR"], "find_in_all_scripts_config.json"
        ),
    )
