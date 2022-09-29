from _shutil import call_echo, get_files

if __name__ == "__main__":
    call_echo(["mpv", get_files()[0]])
