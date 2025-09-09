class Settings:
    need_confirm: bool = True
    need_confirm_edit_file: bool = True

    def __init__(self):
        raise TypeError("Settings class should not be instantiated")
