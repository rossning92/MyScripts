import argparse
import http.client
import json
import urllib.parse
from typing import List

from _script import Script
from utils.menu import Menu


def _match_scripts_with_param(param: str) -> List[str]:
    encoded_param = urllib.parse.quote(param)
    host = "127.0.0.1:4312"
    path = f"/scripts/{encoded_param}"
    conn = http.client.HTTPConnection(host)
    try:
        conn.request("GET", path)
        response = conn.getresponse()
        if response.status == 200:
            data = response.read().decode("utf-8")
            json_data = json.loads(data)
            return [script["path"] for script in json_data["scripts"]]
        else:
            raise Exception(f"Failed to retrieve data: {response.status}")
    finally:
        conn.close()


class ContextMenu(Menu[str]):
    def __init__(self, param: str, **kwargs):
        self.__param = param
        super().__init__(items=_match_scripts_with_param(self.__param), **kwargs)

    def on_created(self):
        if len(self.items) == 1:
            self.on_item_selected(self.items[0])
            self.close()

    def on_item_selected(self, item: str):
        script = Script(item)
        script.execute(args=[self.__param])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("param", type=str)
    args = parser.parse_args()
    ContextMenu(param=args.param).exec()
