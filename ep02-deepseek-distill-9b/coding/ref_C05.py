def sliding_median(nums, k):
    if k <= 0:
        raise ValueError("k")
    if k > len(nums):
        return []
    out = []
    for i in range(len(nums) - k + 1):
        w = sorted(nums[i:i + k])
        if k % 2:
            out.append(float(w[k // 2]))
        else:
            out.append((w[k // 2 - 1] + w[k // 2]) / 2)
    return out
