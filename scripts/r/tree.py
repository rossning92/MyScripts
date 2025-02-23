import argparse
import os


def tree(path=".", dir_only=False) -> str:
    output = ""
    for root, dirs, files in os.walk(path):
        level = root.replace(path, "").count(os.sep)
        indent = " " * 4 * level
        output += f"{indent}{os.path.basename(root)}\n"
        subindent = " " * 4 * (level + 1)
        if not dir_only:
            for f in files:
                if not f.startswith("."):
                    output += f"{subindent}{f}\n"
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dir-only", action="store_true")
    args = parser.parse_args()

    print(tree(dir_only=args.dir_only))
