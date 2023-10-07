from ..menu import Menu


def confirm(message: str):
    menu = Menu(label=message, items=["yes", "no"])
    menu.exec()
    return menu.get_selected_item()
