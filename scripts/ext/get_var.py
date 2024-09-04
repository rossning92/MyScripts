import argparse

from _script import get_variable

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("name", type=str)
    args = parser.parse_args()

    print(get_variable(args.name), end="\n")
