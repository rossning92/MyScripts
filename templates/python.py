#!/usr/bin/env python

"""
A simple python script template.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import with_statement
from io import open
import argparse
import os
import sys


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("infile", help="Input file", type=argparse.FileType("r"))
    parser.add_argument(
        "-o",
        "--outfile",
        help="Output file",
        default=sys.stdout,
        type=argparse.FileType("w"),
    )
    parser.add_argument("--foobar", action="store_true")

    args = parser.parse_args()
