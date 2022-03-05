from _shutil import *

modified_sources = set()


def _revert_file(file):
    print2("Reverting: %s" % file, color="red")
    subprocess.check_call(["hg", "revert", file])


def patch_code(
    file, patt, code, mode="replace", use_regex=False, revert_file=False, count=0
):
    file = os.path.realpath(file)

    if revert_file and file not in modified_sources:
        _revert_file(file)
        modified_sources.add(file)

    s = open(file, "rU").read()

    if code and code in s:
        print2("= %s" % code, color="yellow")
        return

    if not use_regex:
        patt = re.escape(patt)

    matches = re.findall(patt, s)
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
            s = re.sub(re.escape(match), match + "\n" + code, s, count=count)
        elif mode == "before":
            s = re.sub(re.escape(match), code + "\n" + match, s, count=count)
        elif mode == "replace":
            s = re.sub(re.escape(match), code, s, count=count)
        else:
            raise Exception("wrong value in mode param")

    open(file, "w", newline="\n").write(s)


def append_code(file, patt, code, **kwargs):
    patch_code(file, patt, code, mode="after", **kwargs)


def prepend_code(file, patt, code, **kwargs):
    patch_code(file, patt, code, mode="before", **kwargs)


def replace_code(file, patt, code, **kwargs):
    patch_code(file, patt, code, mode="replace", **kwargs)


def read_source(f):
    return open(f, "r", encoding="utf-8").read()


def replace(file, patt, repl, debug_output=False):
    with open(file, "r") as f:
        s = f.read()

    if debug_output:
        for x in re.findall(patt, s):
            print('In file "%s":\n  %s => %s' % (file, x, repl))

    s = re.sub(patt, repl, s)

    with open(file, "w") as f:
        f.write(s)


def prepend_line(file_path, line):
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    if line in lines:
        print("WARNING: line already exists: %s" % line)

    lines[:0] = [line]

    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def append_file(file, s):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            text = f.read()
    else:
        text = ""

    text += "\n" + s

    with open(file, "w", encoding="utf-8") as f:
        f.write(text)
