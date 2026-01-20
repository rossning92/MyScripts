import os

from utils.android import get_main_activity

if __name__ == "__main__":
    activity = get_main_activity(os.environ["PKG_NAME"])
    print(activity)
