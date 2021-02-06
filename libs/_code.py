from _shutil import *

modified_sources = set()


def _revert_file(file):
    print2("Reverting: %s" % file, color="red")
    subprocess.check_call(["hg", "revert", file])


def patch_code(file, patt, code, mode="after", use_regex=False, revert_file=True):
    file = os.path.realpath(file)

    if revert_file and file not in modified_sources:
        _revert_file(file)
        modified_sources.add(file)

    s = open(file, "rU").read()

    if use_regex:
        patt = "^.*" + patt + ".*$"
    else:
        patt = "^.*" + re.escape(patt) + ".*$"

    matches = re.findall(patt, s, re.MULTILINE)
    if not matches:
        print2("ERROR: fail to locate code:\n%s" % patt, color="red")
        sys.exit(1)

    print("## Patching: %s:" % file)
    for match in matches:
        if mode == "after":
            print(match.strip())
        elif mode == "replace":
            print2("- " + match.strip(), color="red")
        print2("+ " + code, color="green")
        if mode == "before":
            print(match.strip())

    for match in set(matches):
        if mode == "after":
            s = re.sub(re.escape(match), match + "\n" + code, s)
        elif mode == "before":
            s = re.sub(re.escape(match), code + "\n" + match, s)
        elif mode == "replace":
            s = re.sub(re.escape(match), code, s)
        else:
            raise Exception("wrong value in mode param")

    open(file, "w", newline="\n").write(s)


def append_code(file, patt, code, revert_file=True):
    patch_code(file, patt, code, mode="after", revert_file=revert_file)


def prepend_code(file, patt, code):
    patch_code(file, patt, code, mode="before")


def replace_code(file, patt, code, revert_file=True, use_regex=False):
    patch_code(
        file, patt, code, mode="replace", revert_file=revert_file, use_regex=use_regex
    )


def read_source(f):
    return open(f, "r", encoding="utf-8").read()
