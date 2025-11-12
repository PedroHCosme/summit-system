"""Utility helpers for working with date strings consistently across the app."""

from __future__ import annotations

from datetime import datetime, date
from typing import Optional

# Accepted input formats (explicit), used as fallbacks after heuristic detection
_EXPLICIT_FORMATS = (
    "%d/%m/%Y",
    "%d/%m/%y",
    "%d-%m-%Y",
    "%d-%m-%y",
    "%Y-%m-%d",
    "%y-%m-%d",
    "%Y%m%d",
)


def _try_parse(value: str, fmt: str) -> Optional[datetime]:
    try:
        return datetime.strptime(value, fmt)
    except (ValueError, TypeError):
        return None


def _parse_by_separator(value: str) -> Optional[datetime]:
    """Parse strings by looking at separators and numeric ranges."""
    if "/" in value:
        parts = value.split("/")
        if len(parts) != 3:
            return None
        day, month, year = parts
        if len(year) == 4:
            return _try_parse(value, "%d/%m/%Y")
        return _try_parse(value, "%d/%m/%y")

    if "-" in value:
        parts = value.split("-")
        if len(parts) != 3:
            return None
        first, second, third = parts
        try:
            first_num = int(first)
            second_num = int(second)
            third_num = int(third)
        except ValueError:
            return None

        if len(first) == 4:
            return _try_parse(value, "%Y-%m-%d")

        if len(third) == 4:
            return _try_parse(value, "%d-%m-%Y")

        # Both two-digit numbers. Decide between DD-MM-YY vs YY-MM-DD
        if second_num > 12:
            return _try_parse(value, "%d-%m-%y")
        if third_num > 31:
            return _try_parse(value, "%y-%m-%d")

        # Ambiguous: attempt YY-MM-DD first, fall back to DD-MM-YY if year < 2020
        temp = _try_parse(value, "%y-%m-%d")
        if temp and temp.year >= 2020:
            return temp
        return _try_parse(value, "%d-%m-%y")

    if value.isdigit() and len(value) == 8:
        return _try_parse(value, "%Y%m%d")

    return None


def parse_date(value: Optional[str]) -> Optional[datetime]:
    """Parse a date string into ``datetime`` (date portion only)."""
    if not value:
        return None

    value = value.strip()
    if not value:
        return None

    parsed = _parse_by_separator(value)
    if parsed:
        return parsed

    for fmt in _EXPLICIT_FORMATS:
        parsed = _try_parse(value, fmt)
        if parsed:
            return parsed

    return None


def parse_date_to_date(value: Optional[str]) -> Optional[date]:
    result = parse_date(value)
    if result:
        return result.date()
    return None


def normalize_date_string(value: Optional[str], output_format: str = "%Y-%m-%d") -> Optional[str]:
    parsed = parse_date(value)
    if not parsed:
        return None
    return parsed.strftime(output_format)


def format_display_date(value: Optional[str | datetime | date]) -> str:
    """Return a human-friendly ``DD/MM/YYYY`` representation."""
    if isinstance(value, str):
        parsed = parse_date(value)
        if not parsed:
            return value or ""
        return parsed.strftime("%d/%m/%Y")
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y")
    if isinstance(value, date):
        return value.strftime("%d/%m/%Y")
    return ""
