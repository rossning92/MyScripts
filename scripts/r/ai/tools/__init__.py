class Settings:
    need_confirm: bool = True
    need_confirm_edit_file: bool = False

    def __init__(self):
        raise TypeError("Settings class should not be instantiated")
