def cb_get_file():
    import win32clipboard

    file_path = None
    win32clipboard.OpenClipboard(None)

    fmt = 0
    while True:
        fmt = win32clipboard.EnumClipboardFormats(fmt)
        if fmt == 0:
            break

        if fmt > 0xC000:
            fmt_name = win32clipboard.GetClipboardFormatName(fmt)
            # print(fmt_name)

            if fmt_name == 'FileNameW':
                data = win32clipboard.GetClipboardData(fmt)
                file_path = data.decode('utf-16').strip('\0x00')

    win32clipboard.CloseClipboard()
    return file_path