from utils.menu import Menu


class MyMenu(Menu):
    def on_focus_gained(self):
        self.set_message("Focus gained")

    def on_focus_lost(self):
        self.set_message("Focus lost")


if __name__ == "__main__":
    menu = MyMenu(
        items=[
            "Apple",
            "Banana",
            "Cherry",
            "Date",
            "Elderberry",
            "Fig",
            "Grape",
            "Honeydew",
            "Kiwi",
            "Lemon",
        ],
        prompt="fruit",
        debug=True,
        wrap_text=True,
        auto_complete=True,
    )
    menu.add_command(lambda: print("alt+z pressed"), hotkey="alt+z")
    menu.add_command(lambda: print("alt+enter pressed"), hotkey="alt+enter")
    menu.add_command(
        lambda: menu.set_message("ctrl+space triggered"), hotkey="ctrl+space"
    )

    menu.exec()
