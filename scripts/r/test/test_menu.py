from utils.menu import Menu

if __name__ == "__main__":
    menu = Menu(
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

    menu.exec()
