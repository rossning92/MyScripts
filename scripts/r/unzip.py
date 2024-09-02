import argparse

from utils.ziputils import unzip

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("src", type=str)
    parser.add_argument("dest", type=str, nargs="?")
    parser.add_argument("--open", action="store_true")
    args = parser.parse_args()

    unzip([args.src], args.dest, open_out_dir=args.open)
