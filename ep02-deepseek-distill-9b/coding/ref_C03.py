import re

_P = re.compile(r'\A\s*(?:([0-9]+)d)?\s*(?:([0-9]+)h)?\s*(?:([0-9]+)m)?\s*(?:([0-9]+)s)?\s*\Z')


def parse_duration(s):
    m = _P.match(s)
    if not m or all(g is None for g in m.groups()):
        return -1
    d, h, mi, sec = [int(g) if g else 0 for g in m.groups()]
    return ((d * 24 + h) * 60 + mi) * 60 + sec
