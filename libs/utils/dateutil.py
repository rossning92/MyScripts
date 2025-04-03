import re
from datetime import datetime
from typing import Optional


def parse_datetime(text: str) -> Optional[datetime]:
    if text.strip().lower() in ["today", "now"]:
        return datetime(datetime.now().year, datetime.now().month, datetime.now().day)

    # Try match date and time.
    match = re.search(
        r"(?:(?P<year>\d{2,4})[-/])?(?P<month>\d{1,2})[-/](?P<day>\d{1,2})"
        r"(\s+(?P<hour>\d{1,2}):(?P<minute>\d{1,2}))?",
        text,
    )
    if match:
        year = int(match.group("year") or datetime.now().year)
        month = int(match.group("month"))
        day = int(match.group("day"))
        hour = int(match.group("hour") or 0)
        minute = int(match.group("minute") or 0)
        return datetime(year, month, day, hour, minute)

    return None
