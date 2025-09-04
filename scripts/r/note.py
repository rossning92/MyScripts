import argparse
import subprocess


def _main():
    parser = argparse.ArgumentParser(description="Open nvim editor")
    parser.add_argument("filepath", nargs="?", help="File path to open", default=None)

    args = parser.parse_args()
    cmd = ["nvim"]
    if args.filepath:
        cmd.append(args.filepath)

    subprocess.run(cmd)


if __name__ == "__main__":
    _main()
