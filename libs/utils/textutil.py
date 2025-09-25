def truncate_text(text: str, max_chars: int = 120) -> str:
    text = text.rstrip().replace("\n", "↵ ")
    return text[:max_chars] + "..." if len(text) > max_chars else text
