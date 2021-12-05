from _shutil import call_echo, get_files

if __name__ == "__main__":
    files = get_files(cd=True)
    files = [x for x in files if x.lower().endswith(".pdf")]
    call_echo(["pdftk"] + files + ["cat", "output", "Combined.pdf"])
