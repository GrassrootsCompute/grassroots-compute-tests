import calendar


def add_months(date_str, n):
    y, m, d = map(int, date_str.split('-'))
    t = y * 12 + (m - 1) + n
    y2, m2 = divmod(t, 12)
    m2 += 1
    d2 = min(d, calendar.monthrange(y2, m2)[1])
    return f"{y2:04d}-{m2:02d}-{d2:02d}"
