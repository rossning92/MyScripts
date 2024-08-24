import argparse

from utils.window import close_window_by_name

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name", help="window name")
    args = parser.parse_args()

    close_window_by_name(name=args.name, all=True)
