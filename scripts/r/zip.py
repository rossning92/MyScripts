import argparse

from utils.ziputils import create_zip_file

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=str)
    parser.add_argument("-o", "--out", type=str, nargs="?")
    args = parser.parse_args()

    create_zip_file(path=args.path, out_file=args.out)
