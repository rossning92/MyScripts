import glob
import os
import sys

from colorama import Fore

kw = r"{{STR_TO_FIND}}"
replacement = r"{{STR_TO_REPLACE}}"


def print_highlight(s, str_highlight):
    s = s.replace(str_highlight, Fore.LIGHTGREEN_EX + str_highlight + Fore.RESET)
    print(s)


def get_all_scripts():
    for file_path in glob.glob("**/*", recursive=True):
        if not os.path.isfile(file_path):
            continue

        yield file_path


if __name__ == "__main__":
    os.chdir("..")

    # Print all matched file names
    matched_file_paths = set()
    for file_path in get_all_scripts():
        if kw in file_path:
            matched_file_paths.add(file_path)
            print_highlight(file_path, kw)

    # Print all occurrence
    matched_files = set()
    for file_path in get_all_scripts():
        try:
            with open(file_path, "r") as f:
                lines = f.readlines()
        except:
            print(
                Fore.RED + "[Warning] failed to read file: %s" % file_path + Fore.RESET
            )
            continue

        line_no = 0
        for l in lines:
            line_no += 1
            if kw in l:
                print_highlight("%s:%d: %s" % (file_path, line_no, l.rstrip()), kw)
                matched_files.add(file_path)

    answer = input('Enter Y to replace "%s" with "%s": ' % (kw, replacement))
    if not answer.lower() == "y":
        sys.exit(1)

    # Replace all occurrence
    for file_path in matched_files:
        with open(file_path, "r") as f:
            s = f.read()

        s = s.replace(kw, replacement)

        with open(file_path, "w") as f:
            f.write(s)

    # rename file names
    for file_path in matched_file_paths:
        new_file_path = file_path.replace(kw, replacement)
        os.rename(file_path, new_file_path)
