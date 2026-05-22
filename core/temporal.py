import datetime
import re

WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def parse_time_range(query: str):
    now = datetime.datetime.now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)

    if re.search(r"\btoday\b", query, re.IGNORECASE):
        return today.timestamp(), now.timestamp()

    if re.search(r"\byesterday\b", query, re.IGNORECASE):
        start = today - datetime.timedelta(days=1)
        return start.timestamp(), today.timestamp()

    for name in WEEKDAYS:
        pattern = rf"\blast\s+{name}\b"
        if re.search(pattern, query, re.IGNORECASE):
            target_idx = WEEKDAYS.index(name)
            current_idx = today.weekday()
            days_back = (current_idx - target_idx) % 7
            if days_back == 0:
                days_back = 7
            start = today - datetime.timedelta(days=days_back)
            end = start + datetime.timedelta(days=1)
            return start.timestamp(), end.timestamp()

    if re.search(r"\bthis\s+week\b", query, re.IGNORECASE):
        start = today - datetime.timedelta(days=today.weekday())
        return start.timestamp(), now.timestamp()

    if re.search(r"\blast\s+week\b", query, re.IGNORECASE):
        mon = today - datetime.timedelta(days=today.weekday())
        start = mon - datetime.timedelta(days=7)
        end = mon
        return start.timestamp(), end.timestamp()

    if re.search(r"\bthis\s+morning\b", query, re.IGNORECASE):
        noon = today.replace(hour=12, minute=0, second=0, microsecond=0)
        return today.timestamp(), noon.timestamp()

    return None


TIME_PATTERNS = [
    r"\btoday\b",
    r"\byesterday\b",
] + [rf"\blast\s+{name}\b" for name in WEEKDAYS] + [
    r"\bthis\s+week\b",
    r"\blast\s+week\b",
    r"\bthis\s+morning\b",
]


def strip_time_expression(query: str) -> str:
    cleaned = query
    for pat in TIME_PATTERNS:
        cleaned = re.sub(pat, "", cleaned, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", cleaned).strip()
