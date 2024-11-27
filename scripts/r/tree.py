import os


def tree(path=".") -> str:
    output = ""
    for root, dirs, files in os.walk(path):
        level = root.replace(path, "").count(os.sep)
        indent = " " * 4 * level
        output += f"{indent}{os.path.basename(root)}\n"
        subindent = " " * 4 * (level + 1)
        for f in files:
            if not f.startswith("."):
                output += f"{subindent}{f}\n"
    return output


if __name__ == "__main__":
    print(tree())
