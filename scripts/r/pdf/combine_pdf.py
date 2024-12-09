#!/bin/bash

import os
import subprocess
import sys

out_file = "combined.pdf"
bookmarks_file = r"C:\tmp\bookmarks.txt"
bookmarks_fmt = (
    "BookmarkBegin\nBookmarkTitle: {}\nBookmarkLevel: 1\nBookmarkPageNumber: {}\n"
)

if os.path.exists(bookmarks_file):
    os.remove(bookmarks_file)
if os.path.exists(out_file):
    os.remove(out_file)

files = sys.argv[1:]
files = [x.replace("\\\\", "\\") for x in files]
print(files)
page_count = 1

# Generate bookmarks file.
with open(bookmarks_file, "w") as bf:
    for f in files:
        title = os.path.basename(os.path.splitext(f)[0])
        bf.write(bookmarks_fmt.format(title, page_count))
        num_pages = (
            subprocess.check_output(["pdftk", f, "dump_data"]).decode("utf-8").strip()
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
    ["pdftk"] + files + ["cat", "output", "out.pdf"],
    # stdout=subprocess.PIPE,
)
p1.wait()
# p2 = subprocess.Popen(
#     ["pdftk", "-", "update_info", bookmarks_file, "output", out_file],
#     stdin=p1.stdout,
# )
# p1.stdout.close()
# p2.wait()
