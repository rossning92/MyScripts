import os

from _script import get_absolute_script_path, get_all_scripts, get_relative_script_path
from _shutil import print2


def replace_script_str(old, new, dry_run=False):
    files = list(get_all_scripts())
    for file in files:
        with open(file, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()

        dirty = False
        for i, line in enumerate(lines):
            if old in line:
                lines[i] = line.replace(old, new)
                if dry_run:
                    if not dirty:
                        print2("%s:" % get_relative_script_path(file), color="black")
                    print("%d: %s" % (i + 1, lines[i]))
                dirty = True

        if dirty and not dry_run:
            s = "\n".join(lines)
            with open(file, "w", encoding="utf-8") as f:
                f.write(s)


if __name__ == "__main__":
    script_full_path = os.environ["SCRIPT"]
    script_rel_path = get_relative_script_path(script_full_path)

    new_script_rel_path = input("Please enter new path for (%s): " % script_rel_path)
    new_script_full_path = get_absolute_script_path(new_script_rel_path)

    replace_script_str(script_rel_path, new_script_rel_path, dry_run=True)

    input("(Press enter to rename...)")
    os.rename(script_full_path, new_script_full_path)
    replace_script_str(script_rel_path, new_script_rel_path)
