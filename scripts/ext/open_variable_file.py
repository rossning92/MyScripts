from _script import get_variable_file
from utils.editor import open_code_editor

if __name__ == "__main__":
    f = get_variable_file()
    open_code_editor(f)
