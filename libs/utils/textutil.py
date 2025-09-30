import os


def truncate_text(text: str, max_chars: int = 120) -> str:
    text = text.rstrip().replace("\n", "↵ ")
    return text[:max_chars] + "..." if len(text) > max_chars else text


def is_text_file(filepath: str, encoding="utf-8", buffer_size=4096, threshold=0.9):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    if os.path.isdir(filepath):
        return False

    try:
        with open(filepath, "rb") as f:
            buffer = f.read(buffer_size)
        if not buffer:
            return True
        decoded = buffer.decode(encoding, errors="replace")
        total_chars = len(decoded)
        if total_chars == 0:
            return True
        invalid_chars = decoded.count("\ufffd")
        valid_ratio = (total_chars - invalid_chars) / total_chars
        return valid_ratio >= threshold
    except Exception as e:
        print(f"An error occurred while checking file {filepath}: {e}")
        return False
