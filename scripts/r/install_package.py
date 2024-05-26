import argparse

from _pkgmanager import get_all_available_packages, require_package
from utils.logger import setup_logger
from utils.menu.select import select_option

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=str, nargs="?", default=None)
    parser.add_argument("-f", "--force", action="store_true", default=False)
    args = parser.parse_args()

    if args.package:
        setup_logger()

        require_package(pkg=args.package, force_install=args.force)

    else:
        # Show all available packages in a menu.
        packages = get_all_available_packages()
        i = select_option(packages)
        if i >= 0:
            require_package(pkg=packages[i], force_install=True)
