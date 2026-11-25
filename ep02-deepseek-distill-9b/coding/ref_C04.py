def merge_intervals(intervals, gap=0):
    xs = sorted([a, b] for a, b in intervals if a <= b)
    out = []
    for a, b in xs:
        if out and a <= out[-1][1] + gap:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out
