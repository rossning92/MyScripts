import os


def truncate_text(text: str, max_chars: int = 120) -> str:
    text = text.rstrip().replace("\n", "↵ ")
    return text[:max_chars] + "..." if len(text) > max_chars else text


def is_text_file(filepath: str, encoding="utf-8", buffer_size=4096):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    if os.path.isdir(filepath):
        return False

    try:
        with open(filepath, "rb") as f:
            buffer = f.read(buffer_size)
            buffer.decode(encoding)
        return True
    except UnicodeDecodeError:
        return False
    except Exception as e:
        print(f"An error occurred while checking file {filepath}: {e}")
        return False
