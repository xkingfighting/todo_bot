"""Natural language date parsing for Chinese and English."""

import re
from datetime import datetime, timedelta

# Weekday mappings
_EN_WEEKDAYS = {
    "monday": 0, "mon": 0, "tuesday": 1, "tue": 1, "wednesday": 2, "wed": 2,
    "thursday": 3, "thu": 3, "friday": 4, "fri": 4, "saturday": 5, "sat": 5,
    "sunday": 6, "sun": 6,
}
_ZH_WEEKDAYS = {
    "一": 0, "二": 1, "三": 2, "四": 3, "五": 4, "六": 5, "日": 6, "天": 6,
}


def parse_natural_date(text: str) -> tuple[str | None, str]:
    """Parse natural language date from text.

    Returns (date_str_YYYY-MM-DD or None, cleaned_text).
    """
    today = datetime.now()
    original = text

    # Try explicit @YYYY-MM-DD first
    m = re.search(r'@(\d{4}-\d{2}-\d{2})', text)
    if m:
        try:
            datetime.strptime(m.group(1), "%Y-%m-%d")
            return m.group(1), text.replace(m.group(0), "").strip()
        except ValueError:
            pass

    # Try @YYYY-MM-DD HH:MM
    m = re.search(r'@(\d{4}-\d{2}-\d{2})\s+(\d{1,2}:\d{2})', text)
    if m:
        return m.group(1), text.replace(m.group(0), "").strip()

    lower = text.lower()

    # English patterns
    en_map = {
        "today": 0, "tonight": 0,
        "tomorrow": 1, "tmr": 1, "tmrw": 1,
        "day after tomorrow": 2,
    }
    for word, delta in en_map.items():
        if word in lower:
            d = (today + timedelta(days=delta)).strftime("%Y-%m-%d")
            cleaned = re.sub(re.escape(word), "", text, flags=re.IGNORECASE).strip()
            return d, cleaned

    # "next Monday", "this Friday"
    m = re.search(r'(?:next|this)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday'
                  r'|mon|tue|wed|thu|fri|sat|sun)', lower)
    if m:
        target_wd = _EN_WEEKDAYS[m.group(1)]
        days_ahead = (target_wd - today.weekday()) % 7
        if "next" in m.group(0):
            days_ahead += 7 if days_ahead <= 0 else 0
            if days_ahead == 0:
                days_ahead = 7
        else:
            if days_ahead == 0:
                days_ahead = 7
        d = (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
        cleaned = text[:m.start()] + text[m.end():]
        return d, cleaned.strip()

    # "in N days/weeks"
    m = re.search(r'in\s+(\d+)\s+(day|days|week|weeks|month|months)', lower)
    if m:
        n = int(m.group(1))
        unit = m.group(2)
        if "day" in unit:
            d = (today + timedelta(days=n)).strftime("%Y-%m-%d")
        elif "week" in unit:
            d = (today + timedelta(weeks=n)).strftime("%Y-%m-%d")
        else:
            month = today.month + n
            year = today.year + (month - 1) // 12
            month = (month - 1) % 12 + 1
            d = today.replace(year=year, month=month).strftime("%Y-%m-%d")
        cleaned = text[:m.start()] + text[m.end():]
        return d, cleaned.strip()

    # Chinese patterns
    zh_map = {
        "今天": 0, "今晚": 0,
        "明天": 1, "明日": 1,
        "后天": 2, "後天": 2,
        "大后天": 3, "大後天": 3,
    }
    for word, delta in zh_map.items():
        if word in text:
            d = (today + timedelta(days=delta)).strftime("%Y-%m-%d")
            return d, text.replace(word, "").strip()

    # "下周一", "这周五", "本周三"
    m = re.search(r'(下|这|本)周([一二三四五六日天])', text)
    if m:
        prefix = m.group(1)
        target_wd = _ZH_WEEKDAYS[m.group(2)]
        days_ahead = (target_wd - today.weekday()) % 7
        if prefix == "下":
            days_ahead += 7 if days_ahead <= 0 else 0
            if days_ahead == 0:
                days_ahead = 7
        else:
            if days_ahead == 0:
                days_ahead = 7
        d = (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
        return d, text[:m.start()] + text[m.end():]

    # "N天后", "N周后"
    m = re.search(r'(\d+)\s*(天|周|个月)后', text)
    if m:
        n = int(m.group(1))
        unit = m.group(2)
        if unit == "天":
            d = (today + timedelta(days=n)).strftime("%Y-%m-%d")
        elif unit == "周":
            d = (today + timedelta(weeks=n)).strftime("%Y-%m-%d")
        else:
            month = today.month + n
            year = today.year + (month - 1) // 12
            month = (month - 1) % 12 + 1
            d = today.replace(year=year, month=month).strftime("%Y-%m-%d")
        return d, text[:m.start()] + text[m.end():]

    # "下个月", "下月"
    if "下个月" in text or "下月" in text:
        month = today.month % 12 + 1
        year = today.year + (1 if today.month == 12 else 0)
        d = today.replace(year=year, month=month, day=1).strftime("%Y-%m-%d")
        return d, text.replace("下个月", "").replace("下月", "").strip()

    return None, original


def parse_time(text: str) -> tuple[str | None, str]:
    """Extract HH:MM time from text. Returns (time_str or None, cleaned_text)."""
    m = re.search(r'(\d{1,2}):(\d{2})', text)
    if m:
        h, mi = int(m.group(1)), int(m.group(2))
        if 0 <= h <= 23 and 0 <= mi <= 59:
            return f"{h:02d}:{mi:02d}", text[:m.start()] + text[m.end():]

    # Chinese: "下午3点", "上午10点半"
    m = re.search(r'(上午|下午|晚上)?(\d{1,2})点(半|\d{1,2}分)?', text)
    if m:
        h = int(m.group(2))
        mi = 30 if m.group(3) == "半" else (int(m.group(3).replace("分", "")) if m.group(3) and m.group(3) != "半" else 0)
        period = m.group(1)
        if period in ("下午", "晚上") and h < 12:
            h += 12
        if 0 <= h <= 23 and 0 <= mi <= 59:
            return f"{h:02d}:{mi:02d}", text[:m.start()] + text[m.end():]

    return None, text
