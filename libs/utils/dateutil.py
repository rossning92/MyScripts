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
        "^"
        r"(?:(?P<year>\d{2,4})[-/])?"
        r"(?:(?P<month>\d{1,2})[-/](?P<day>\d{1,2}))?"
        r"(?:\s+(?P<hour>\d{1,2})(?::(?P<minute>\d{1,2}))?(?P<ampm>am|pm)?)?"
        "$",
        text_lower,
    )
    if match:
        now = datetime.now()
        year = int(match.group("year") or now.year)
        month = int(match.group("month") or now.month)
        day = int(match.group("day") or now.day)
        hour = int(match.group("hour") or 0)
        minute = int(match.group("minute") or 0)
        ampm = match.group("ampm")

        # Adjust hour for AM/PM if specified
        if ampm:
            if ampm == "pm" and hour < 12:
                hour += 12
            elif ampm == "am" and hour == 12:
                hour = 0

        return datetime(year, month, day, hour, minute)

    return None


def format_datetime(dt: datetime, show_year: bool = False, show_hhmm=True) -> str:
    format = "%Y-%m-%d" if show_year else "%m-%d"
    if show_hhmm:
        format += "" if (dt.hour == 0 and dt.minute == 0) else " %H:%M"
    return dt.strftime(format)


def format_timestamp(ts: float, show_year: bool = False) -> str:
    dt = datetime.fromtimestamp(ts)
    return format_datetime(dt=dt, show_year=show_year)
