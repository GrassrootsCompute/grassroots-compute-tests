from datetime import date


def month_bounds(year, month):
    """Return (first day of the month, first day of the NEXT month). The end bound is exclusive."""
    start = date(year, month, 1)
    end = date(year + (month == 12), month % 12 + 1, 1)
    return start, end


def in_period(d, start, end):
    """True when start <= d < end. Use this for every period filter (CONVENTIONS.md section 2)."""
    return start <= d < end
