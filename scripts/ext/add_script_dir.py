from _script import add_script_dir
from _shutil import get_current_folder

if __name__ == "__main__":
    script_dir = get_current_folder()
    prefix = input("prefix: ")
    add_script_dir(script_dir, prefix=prefix)
