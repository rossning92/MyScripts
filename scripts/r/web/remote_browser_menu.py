import webbrowser

import requests
from utils.menu import Menu


class Page:
    def __init__(self, data):
        self.data = data
        self.title = data.get("title", "")
        self.url = data.get("url", "")


class RemoteBrowserMenu(Menu[Page]):
    def __init__(self, **kwargs):
        r = requests.get("http://127.0.0.1:21222/json")
        items = [Page(item) for item in r.json()]
        super().__init__(items=items, **kwargs)

    def get_item_text(self, item: Page) -> str:
        return item.title

    def on_item_selected(self, item: Page):
        requests.get(f"http://127.0.0.1:21222/json/activate/{item.data['id']}")

        url = item.data.get("devtoolsFrontendUrl")
        if url:
            if url.startswith("/"):
                url = "http://127.0.0.1:21222" + url
            webbrowser.open(url)


if __name__ == "__main__":
    menu = RemoteBrowserMenu()
    menu.exec()
