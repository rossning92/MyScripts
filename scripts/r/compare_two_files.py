from _shutil import get_files, call_echo

if __name__ == "__main__":
    files = get_files()
    assert len(files) == 2

    vscode = r"C:\Program Files\Microsoft VS Code\Code.exe"
    call_echo([vscode, "--diff", files[0], files[1]])
