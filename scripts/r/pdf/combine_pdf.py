#!/bin/bash

import datetime
import os
import subprocess
import sys

generate_bookmark = False

current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
out_file = f"combined_{current_time}.pdf"

bookmarks_file = r"bookmarks.txt"
bookmarks_fmt = (
    "BookmarkBegin\nBookmarkTitle: {}\nBookmarkLevel: 1\nBookmarkPageNumber: {}\n"
)

files = sys.argv[1:]
files = [x.replace("\\\\", "\\") for x in files]
files = [file for file in files if file.lower().endswith(".pdf")]
files = sorted(files)
print("Input Files:")
for file in files:
    print(f" - {file}")

if generate_bookmark:
    if os.path.exists(bookmarks_file):
        os.remove(bookmarks_file)
    if os.path.exists(out_file):
        os.remove(out_file)

    # Generate bookmarks file.
    page_count = 1
    with open(bookmarks_file, "w") as bf:
        for f in files:
            title = os.path.basename(os.path.splitext(f)[0])
            bf.write(bookmarks_fmt.format(title, page_count))
            num_pages = (
                subprocess.check_output(["pdftk", f, "dump_data"])
                .decode("utf-8")
                .strip()
            )
            num_pages = int(
                [
                    line.split(":")[1]
                    for line in num_pages.split("\n")
                    if "NumberOfPages" in line
                ][0]
            )
            page_count += num_pages


# Combine PDFs and embed the generated bookmarks file.
p1 = subprocess.Popen(
    ["pdftk"] + files + ["cat", "output", out_file],
    # stdout=subprocess.PIPE,
)
p1.wait()
# p2 = subprocess.Popen(
#     ["pdftk", "-", "update_info", bookmarks_file, "output", out_file],
#     stdin=p1.stdout,
# )
# p1.stdout.close()
# p2.wait()
