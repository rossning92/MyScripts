import argparse
import os

from utils.dotenv import set_dotenv
from utils.script.path import get_data_dir

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("key", type=str)
    parser.add_argument("value", type=str)
    args = parser.parse_args()

    set_dotenv(args.key, args.value, dotenv_path=os.path.join(get_data_dir(), ".env"))
