import argparse

from _pkgmanager import get_all_available_packages, require_package
from utils.menu.select import select_option

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=str, nargs="?", default=None)
    args = parser.parse_args()

    if args.package:
        require_package(pkg=args.package)

    else:
        # Show all available packages in a menu.
        packages = get_all_available_packages()
        i = select_option(packages)
        if i >= 0:
            require_package(pkg=packages[i], force_install=True)
