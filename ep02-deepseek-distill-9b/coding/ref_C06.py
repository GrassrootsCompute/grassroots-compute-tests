def _parse(v):
    v = v.strip()
    if v[:1] in ('v', 'V'):
        v = v[1:]
    main, sep, pre = v.partition('-')
    nums = [int(x) for x in main.split('.')]
    return nums, (pre if sep else None)


def compare_versions(a, b):
    na, pa = _parse(a)
    nb, pb = _parse(b)
    n = max(len(na), len(nb))
    na += [0] * (n - len(na))
    nb += [0] * (n - len(nb))
    if na != nb:
        return 1 if na > nb else -1
    if pa == pb:
        return 0
    if pa is None:
        return 1
    if pb is None:
        return -1
    return 1 if pa > pb else -1
