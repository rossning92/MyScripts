from utils.editor import open_code_editor
from utils.script.path import get_variable_file

if __name__ == "__main__":
    f = get_variable_file()
    open_code_editor(f)
