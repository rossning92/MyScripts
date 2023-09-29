import argparse

from _pkgmanager import require_package

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=str)
    args = parser.parse_args()

    require_package(pkg=args.package)
