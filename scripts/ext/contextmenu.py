import argparse
import http.client
import json
import urllib.parse
from dataclasses import dataclass
from typing import List

from _script import Script
from utils.menu import Menu


@dataclass
class _MatchedScript:
    name: str
    path: str
    match: str

    def __str__(self) -> str:
        return self.name


def _match_scripts_with_param(param: str) -> List[_MatchedScript]:
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
            return [
                _MatchedScript(
                    name=script["name"],
                    path=script["path"],
                    match=script["match"],
                )
                for script in json_data["scripts"]
            ]
        else:
            raise Exception(f"Failed to retrieve data: {response.status}")
    finally:
        conn.close()


class ContextMenu(Menu[_MatchedScript]):
    def __init__(self, param: str, **kwargs):
        super().__init__(
            prompt=f"({param})",
            items=_match_scripts_with_param(param),
            **kwargs,
        )

    def on_created(self):
        if len(self.items) == 1:
            self.on_item_selected(self.items[0])
            self.close()

    def on_item_selected(self, item: _MatchedScript):
        script = Script(item.path)
        script.execute(args=[item.match])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("param", type=str)
    args = parser.parse_args()
    ContextMenu(param=args.param).exec()
