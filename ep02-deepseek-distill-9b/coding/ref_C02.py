def split_bill(total_cents, weights):
    if any(w < 0 for w in weights):
        raise ValueError("negative weight")
    if not weights:
        return []
    s = sum(weights)
    if s == 0:
        raise ValueError("zero sum")
    base = [total_cents * w // s for w in weights]
    rem = total_cents - sum(base)
    order = sorted(range(len(weights)), key=lambda i: (-(total_cents * weights[i] % s), i))
    for i in order[:rem]:
        base[i] += 1
    return base
