"""独立重算每题答案（暴力/模拟/数值法），与 answers.json 比对；编程题跑参考答案过隐藏测试。
运行：python3 -I verify.py"""
import itertools, json, math, os, shutil, subprocess, sys, tempfile
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction as F

HERE = os.path.dirname(os.path.abspath(__file__))
ANS = json.load(open(os.path.join(HERE, "answers.json"), encoding="utf-8"))


def fmt(x, p):
    return str(Decimal(repr(float(x))).quantize(Decimal(1).scaleb(-p), rounding=ROUND_HALF_UP))


calc = {}

# ---- M01-M10：逐项模拟 ----
def m01():
    t = 0.0
    for i in range(180):  # 每度电
        if i < 72: t += 1.2 + 0.15
        else: t += 0.45
    return t * 0.9
def m02():
    cost = sum(120 for _ in range(12)) + sum(80 for _ in range(8))
    cooked = 20 - 20 * 0.2
    for price in range(1, 1000):
        if price * cooked >= cost * 1.3 - 1e-9: return price
def m03():
    done, day = F(0), 0
    while done < 1:
        day += 1
        done += (F(1, 20) + F(1, 30)) if day <= 6 else (F(4, 5) * F(1, 30) + F(1, 75))
        if done >= 1:
            over = done - 1
            rate = (F(4, 5) * F(1, 30) + F(1, 75))
            return day - float(over / rate)
def m04():
    for sec in range(0, 4 * 3600):
        t = sec / 60
        if t <= 90: a = 280 / 60 * t
        elif t <= 100: a = 420
        else: a = 420 + 280 / 60 * (t - 100)
        b = 830 - (240 / 60 * (t - 30) if t > 30 else 0)
        if a >= b: return round(t)
def m05():
    p = 7200 * 85 / 100
    if p >= 6000: p -= 600
    sub = min(p * 15 / 100, 1500)
    return p - sub
def m06():
    mons = {"a": [(50, 12)], "b": [(30, 12)], "c": [(20, 3)], "d": [(40, 9)]}
    sh = {k: sum(c * m for c, m in v) for k, v in mons.items()}
    return 138 * sh["d"] / sum(sh.values())
def m07():
    days = [28] * 5 + [36, 42]
    tot = 0
    for i, n in enumerate(days):
        inc = sum(6.5 + (2.5 if k > 30 else 0) for k in range(1, n + 1))
        if i == 6: inc *= 1.5
        tot += inc
    return tot * 0.92
def m08():
    bal = 100000.0
    for _ in range(12): bal += bal * (0.048 / 12)
    return bal - (bal - 100000) * 0.2
def m09():
    sol, conc = 500.0, 0.12 * 500
    for _ in range(3):
        conc -= conc * 100 / sol
    return conc / sol * 100
def m10():
    w, h = 30, 0
    while w < 224:
        h += 1
        w += (12 - 15) if h <= 2 else (12 + 8 - 15)
    return h
for k, f, p in [("M01", m01, 2), ("M02", m02, None), ("M03", m03, 1), ("M04", m04, None), ("M05", m05, 2),
                ("M06", m06, 2), ("M07", m07, 2), ("M08", m08, 2), ("M09", m09, 2), ("M10", m10, None)]:
    v = f(); calc[k] = (fmt(v, p) if p is not None else str(int(v)), v)

# ---- M11-M20 ----
calc["M11"] = (str(v := sum(n for n in range(1, 20000) if (n * n + 2026) % (n + 26) == 0)), v)
def m12():
    return sum(1 for s in itertools.product("012", repeat=8)
               if all(s[i] != s[i + 1] for i in range(7)) and s.count("0") == 3)
calc["M12"] = (str(v := m12()), v)
def m13():  # 吸收马尔可夫链迭代
    from collections import defaultdict
    dist = {"": F(1)}; pa = F(0); pb = F(0)
    for _ in range(120):
        nd = defaultdict(F)
        for st, pr in dist.items():
            for c in "HT":
                s = (st + c)[-3:]
                if s == "HTH": pa += pr / 2
                elif s == "HHT": pb += pr / 2
                else: nd[s] += pr / 2
        dist = nd
    return pa / (pa + pb)
v = m13(); fr = F(v).limit_denominator(1000); calc["M13"] = (f"{fr.numerator}/{fr.denominator}", fr)
def m14():
    a, b = 1, 2
    for _ in range(2024): a, b = b, (b + 2 * a) % 11
    return b % 11 if True else 0
# a1=1,a2=2：迭代 2024 次后 b 即 a_2026
calc["M14"] = (str(v := m14()), v)
def m15():
    best = 1e9
    for i in range(1, 140000):
        x = i / 10000
        y = (15 - x) / (1 + x)
        if y > 0: best = min(best, x + 2 * y)
    return best
v = m15(); calc["M15"] = ("grid", v)
def m16():
    A, B = (0.0, 0.0), (20.0, 0.0)
    # C 距 A=15, 距 B=7
    cx = (15**2 - 7**2 + 20**2) / (2 * 20); cy = math.sqrt(15**2 - cx**2); C = (cx, cy)
    a, b, c = 7, 15, 20  # a=BC, b=CA, c=AB
    I = ((a * A[0] + b * B[0] + c * C[0]) / 42, (a * A[1] + b * B[1] + c * C[1]) / 42)
    # 外心：垂直平分线
    ox = 10.0; oy = (cx**2 + cy**2 - 20 * cx) / (2 * cy)
    return math.hypot(I[0] - ox, I[1] - oy)
calc["M16"] = (fmt(v := m16(), 4), v)
calc["M17"] = (str(v := sum(1 for n in range(1, 2027) if [n % 2 == 0, n % 3 == 0, n % 5 == 0].count(True) == 1)), v)
def m18():
    cnt = 0
    def go(rem, last):
        nonlocal cnt
        if rem == 0: cnt += 1; return
        for m in (1, 2, 3):
            if m <= rem and not (m == 3 and last == 3): go(rem - m, m)
    go(10, 0); return cnt
calc["M18"] = (str(v := m18()), v)
def m19():
    balls = ["R"] * 5 + ["B"] * 4 + ["G"] * 3
    good = tot = 0
    for seq in itertools.permutations(range(12), 4):
        tot += 1
        if len({balls[i] for i in seq}) == 2: good += 1
    return F(good, tot)
v = m19(); calc["M19"] = (f"{v.numerator}/{v.denominator}", v)
def m20():
    s = 0
    for a in range(3, 12):
        for b in range(a + 1, 200):
            for c in range(b + 1, 2000):
                if F(1, a) + F(1, b) + F(1, c) == F(1, 2): s += c
    return s
calc["M20"] = (str(v := m20()), v)

# ---- S01-S10（用数值积分/求根等不同路径）----
def s01():
    g, th = 9.8, math.radians(30)
    # 沿斜面用小步长积分
    dt, x, vel = 1e-6, 0.0, 0.0
    a = g * math.sin(th) - 0.2 * g * math.cos(th)
    while x < 4.0:
        vel += a * dt; x += vel * dt
    # 水平：能量法 mu*g*s = v^2/2
    return vel**2 / 2 / (0.2 * g)
v = s01(); calc["S01"] = (fmt(v, 2), v)
def s02():
    # 网格电流求解：I 使 emf = I*(1+2) + V并联，V并联=I*R并
    lo, hi = 0.0, 10.0
    for _ in range(200):
        I = (lo + hi) / 2
        Rpar = 1 / (1 / 4 + 1 / 6)
        if I * (1 + 2 + Rpar) > 12: hi = I
        else: lo = I
    V = I * (1 / (1 / 4 + 1 / 6))
    return V * V / 6
v = s02(); calc["S02"] = (fmt(v, 2), v)
def s03():
    lo, hi = 0.0, 100.0
    for _ in range(200):
        T = (lo + hi) / 2
        # 以 0°C 为参考的总热量：铜+水+冰(含熔化)
        heat_total = 0.5 * 390 * (80 - 0) + 2.0 * 4200 * 15  # 初始相对 0°C
        cur = (0.5 * 390 + 2.0 * 4200 + 0.1 * 4200) * T + 0.1 * 3.34e5
        if cur > heat_total: hi = T
        else: lo = T
    return T
v = s03(); calc["S03"] = (fmt(v, 1), v)
def s04():
    from fractions import Fraction as Fr
    u1, f1 = Fr(40), Fr(15)
    v1 = 1 / (1 / f1 - 1 / u1)
    u2 = Fr(30) - v1; f2 = Fr(-20)
    return float(1 / (1 / f2 - 1 / u2))
v = s04(); calc["S04"] = (fmt(v, 2), v)
def s05():
    # 能量/动量：v0 来自能量；碰后动量守恒；滑行用 v^2=2as 的 a
    v0 = math.sqrt(2 * 10 * 1.25)
    v = (0.2 * v0) / (0.2 + 0.3)
    a = 0.25 * 10
    s = 0.0
    while v > 0:
        s += v * 1e-6; v -= a * 1e-6
    return s
v = s05(); calc["S05"] = (fmt(v, 2), v)
def s06():
    mol_hcl = 0.5 * 0.2
    mol_caco3 = 0.896 / 22.4
    left = mol_hcl - 2 * mol_caco3
    assert mol_caco3 * 100.09 <= 5.00
    return left / 0.2
v = s06(); calc["S06"] = (fmt(v, 3), v)
def s07():
    mass_needed = 0.5 * 0.25 * 98.0
    return mass_needed / 0.98 / 1.84
v = s07(); calc["S07"] = (fmt(v, 2), v)
def s08():
    c0 = 0.2
    lo, hi = 0.0, c0
    for _ in range(200):
        x = (lo + hi) / 2
        if (2 * x) ** 2 / (c0 - x) > 0.36: hi = x
        else: lo = x
    return x / c0 * 100
v = s08(); calc["S08"] = (fmt(v, 1), v)
def s09():
    Ka = 1.8e-5; HA0, Ac0 = 0.030, 0.020  # 混合后（总 0.2 L）
    lo, hi = 1e-8, 1e-2
    for _ in range(200):  # 精确解：h = Ka*(HA0-h)/(Ac0+h)
        h = (lo * hi) ** 0.5
        if h * (Ac0 + h) > Ka * (HA0 - h): hi = h
        else: lo = h
    return -math.log10(h)
v = s09(); calc["S09"] = (fmt(v, 2), v)
def s10():
    Q = 2.00 * 1800
    mol_e = Q / 96485
    mol_o2 = mol_e / 4
    return mol_o2 * 22.4 * 1000
v = s10(); calc["S10"] = (fmt(v, 1), v)

# ---- 比对 ----
bad = 0
def show(qid, ok, mine, theirs, raw=""):
    global bad
    print(f"{'✓' if ok else '✗'} {qid}  答案={theirs}  重算={mine} {raw}")
    if not ok: bad += 1

for qid, meta in ANS.items():
    if meta["kind"] == "code": continue
    mine, raw = calc[qid]
    if qid == "M15":
        ok = abs(raw - 8 * math.sqrt(2) + 3) < 1e-3 and fmt(8 * math.sqrt(2) - 3, 4) == meta["answer"]
        show(qid, ok, f"{raw:.6f}(网格)", meta["answer"]); continue
    show(qid, mine == meta["answer"], mine, meta["answer"], f"(原值 {raw})" if meta["kind"] == "decimal" else "")

# ---- 编程题：参考答案过隐藏测试 ----
cdir = os.path.join(HERE, "coding")
for qid in sorted(k for k, m in ANS.items() if m["kind"] == "code"):
    tmp = tempfile.mkdtemp()
    try:
        shutil.copy(os.path.join(cdir, f"ref_{qid}.py"), os.path.join(tmp, "solution.py"))
        shutil.copy(os.path.join(cdir, f"test_{qid}.py"), os.path.join(tmp, f"test_{qid}.py"))
        code = f"import sys,unittest; sys.path.insert(0,{tmp!r}); unittest.main(module='test_{qid}', argv=['x'])"
        r = subprocess.run([sys.executable, "-I", "-c", code], cwd=tmp, capture_output=True, text=True, timeout=60)
        import re as _re
        mm = _re.search(r"Ran (\d+) test", r.stderr); n = mm.group(1) if mm else "?"
        show(qid, r.returncode == 0, "参考答案通过", "隐藏测试", f"(unittest 运行 {n} 个测试方法)")
        if r.returncode: print(r.stderr[-800:])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

print("\n全部一致 ✓" if not bad else f"\n有 {bad} 题不一致 ✗")
sys.exit(1 if bad else 0)
