import argparse

from utils.window import activate_window_by_name

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Activate window by name.")
    parser.add_argument("name", help="Window name or regex pattern")
    args = parser.parse_args()

    activate_window_by_name(args.name)
