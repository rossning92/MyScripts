import logging
import sys
import re
from _shutil import  get_newest_file


if __name__ == "__main__":
    url = sys.argv[-1]

    # Remove anything after "&": https://www.youtube.com/watch?v=xxxxxxxx&list=yyyyyyyy&start_radio=1
    url = re.sub(r"(\?(?!v)|&).*$", "", url)

    url_file = get_newest_file("*.*") + ".url"
    logging.info("Save url to: %s" % url_file)
    with open(url_file, "w", encoding="utf-8") as f:
        f.write(url)