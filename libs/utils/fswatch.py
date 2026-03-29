import ctypes
import ctypes.wintypes as wintypes
import os
import sys

# Windows constants
FILE_LIST_DIRECTORY = 0x0001
OPEN_EXISTING = 3
FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
FILE_SHARE_READ = 0x01
FILE_SHARE_WRITE = 0x02
FILE_SHARE_DELETE = 0x04

FILE_NOTIFY_CHANGE_FILE_NAME = 0x01
FILE_NOTIFY_CHANGE_DIR_NAME = 0x02
FILE_NOTIFY_CHANGE_SIZE = 0x08
FILE_NOTIFY_CHANGE_LAST_WRITE = 0x10

ACTIONS = {
    1: "CREATED",
    2: "DELETED",
    3: "MODIFIED",
    4: "RENAMED_FROM",
    5: "RENAMED_TO",
}

kernel32 = ctypes.windll.kernel32
CreateFileW = kernel32.CreateFileW
CreateFileW.restype = wintypes.HANDLE
ReadDirectoryChangesW = kernel32.ReadDirectoryChangesW
CloseHandle = kernel32.CloseHandle

INVALID_HANDLE_VALUE = wintypes.HANDLE(-1).value


def watch_directory(path, recursive=True, stop_event=None):
    """Yield (action, filepath) tuples for changes under `path`."""
    handle = CreateFileW(
        path,
        FILE_LIST_DIRECTORY,
        FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
        None,
        OPEN_EXISTING,
        FILE_FLAG_BACKUP_SEMANTICS,
        None,
    )
    if handle == INVALID_HANDLE_VALUE:
        raise OSError(f"Cannot open directory: {path}")

    buf = ctypes.create_string_buffer(65536)
    notify_filter = (
        FILE_NOTIFY_CHANGE_FILE_NAME
        | FILE_NOTIFY_CHANGE_DIR_NAME
        | FILE_NOTIFY_CHANGE_SIZE
        | FILE_NOTIFY_CHANGE_LAST_WRITE
    )

    try:
        while stop_event is None or not stop_event.is_set():
            bytes_returned = wintypes.DWORD(0)
            ok = ReadDirectoryChangesW(
                handle,
                buf,
                len(buf),
                recursive,
                notify_filter,
                ctypes.byref(bytes_returned),
                None,  # synchronous
                None,
            )
            if not ok:
                break

            offset = 0
            while True:
                fni = buf.raw[offset:]
                next_offset = int.from_bytes(fni[0:4], "little")
                action = int.from_bytes(fni[4:8], "little")
                name_len = int.from_bytes(fni[8:12], "little")
                filename = fni[12 : 12 + name_len].decode("utf-16-le")

                action_str = ACTIONS.get(action, f"UNKNOWN({action})")
                full_path = os.path.join(path, filename)
                yield action_str, full_path

                if next_offset == 0:
                    break
                offset += next_offset
    finally:
        CloseHandle(handle)


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "."
    print(f"Monitoring: {path}", flush=True)
    print("Press Ctrl+C to stop.\n", flush=True)

    try:
        for action, filepath in watch_directory(path, recursive=True):
            print(f"[{action:12s}] {filepath}", flush=True)
    except KeyboardInterrupt:
        print("\nStopped.")
