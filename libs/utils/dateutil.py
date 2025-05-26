import re
from datetime import datetime, timedelta
from typing import Optional


def parse_datetime(text: str) -> Optional[datetime]:
    text_lower = text.strip().lower()

    weekdays = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }
    if text_lower in weekdays:
        now = datetime.now()
        current_weekday = now.weekday()
        target_weekday = weekdays[text_lower]
        days_ahead = target_weekday - current_weekday
        if days_ahead <= 0:  # Target weekday has passed this week
            days_ahead += 7
        next_day = now + timedelta(days=days_ahead)
        return datetime(next_day.year, next_day.month, next_day.day)
    elif text_lower == "today":
        now = datetime.now()
        return datetime(now.year, now.month, now.day)
    elif text_lower == "tomorrow":
        tomorrow = datetime.now() + timedelta(days=1)
        return datetime(tomorrow.year, tomorrow.month, tomorrow.day)

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


def format_timestamp(ts: float, include_year: bool = True) -> str:
    dt = datetime.fromtimestamp(ts)
    date_format = "%Y-%m-%d" if include_year else "%m-%d"
    time_format = "" if (dt.hour == 0 and dt.minute == 0) else " %H:%M"
    return dt.strftime(date_format + time_format)
