import argparse

from _script import set_variable

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("name", type=str)
    parser.add_argument("value", type=str)
    args = parser.parse_args()

    set_variable(args.name, args.value)
