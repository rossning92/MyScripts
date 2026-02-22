import re
from typing import Any, Dict, Optional, Tuple

from utils.yaml import parse_yaml


def parse_front_matter(text: str) -> Tuple[Optional[Dict[str, Any]], str]:
    """
    Extract front matter from a markdown string.
    Returns a tuple of (metadata_dict, content_string).
    If no front matter is found, metadata_dict is None.
    """
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n?", text, re.DOTALL)
    if match:
        metadata = parse_yaml(match.group(1))
        content = text[match.end() :].strip()
        return metadata, content
    return None, text.strip()
