import os

from _script import get_absolute_script_path, get_all_scripts, get_relative_script_path
from _shutil import print2, set_clip


def replace_script_str(old, new, dry_run=False):
    if dry_run:
        print("To be replaced:")

    files = list(get_all_scripts())
    for file in files:
        with open(file, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()

        dirty = False
        for i, line in enumerate(lines):
            if old in line:
                if dry_run:
                    print2(
                        "%s:%d:" % (get_relative_script_path(file), i + 1),
                        color="blue",
                        end="",
                    )
                    print(lines[i])

                    dirty = True
                else:
                    lines[i] = line.replace(old, new)
                    dirty = True

        if dirty and not dry_run:
            s = "\n".join(lines)
            with open(file, "w", encoding="utf-8") as f:
                f.write(s)


if __name__ == "__main__":
    script_full_path = os.environ["SCRIPT"]
    script_rel_path = get_relative_script_path(script_full_path)

    replace_script_str(script_rel_path, None, dry_run=True)
    set_clip(script_rel_path)
    new_script_rel_path = input(
        '\nEnter new path for "%s" (^v to paste): ' % script_rel_path
    )
    new_script_full_path = get_absolute_script_path(new_script_rel_path)

    input("(Press enter to rename...)")
    os.makedirs(os.path.dirname(new_script_full_path), exist_ok=True)
    os.rename(script_full_path, new_script_full_path)

    # Rename config file if any
    config_file = os.path.splitext(script_full_path)[0] + ".config.yaml"
    new_config_file = os.path.splitext(new_script_full_path)[0] + ".config.yaml"
    if os.path.exists(config_file):
        os.rename(config_file, new_config_file)

    replace_script_str(script_rel_path, new_script_rel_path)
