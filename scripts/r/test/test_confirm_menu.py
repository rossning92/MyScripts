from utils.menu.confirmmenu import ConfirmMenu

if __name__ == "__main__":
    menu = ConfirmMenu()
    menu.exec()
    print(menu.is_confirmed())
