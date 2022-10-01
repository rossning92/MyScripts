from _editor import open_in_vscode
from _script import get_variable_file

if __name__ == "__main__":
    f = get_variable_file()
    open_in_vscode(f)
