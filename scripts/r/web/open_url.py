#!/usr/bin/env python

import argparse

from _browser import open_url

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", type=str)
    args = parser.parse_args()

    open_url(args.url)
