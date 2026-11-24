import importlib, json, os, random, sys
from datetime import date, timedelta
from decimal import Decimal
B5 = sys.argv[1]
sys.path.insert(0, os.path.join(B5, "ref"))
from core.model import Txn
from core.errors import ReportError
names = json.load(open(os.path.join(B5, "answer.json")))["modules"]
mods = {n: importlib.import_module("reports." + n) for n in names}
CATS = ["groceries","dining","transport","rent","utilities","health","travel","gifts","education","fitness","pets","books","coffee","subscriptions","insurance","other"]
MERCH = ["Marketa","SaveMart","Rideo","Zed Fuel","Sparko","Mercuro","Air Nine","Shopmart","Depot Store","Maple Books","Petzone","Iron Gym","Netflix","Spotify","Shield Health"]
def dataset(seed):
    r = random.Random(seed); out = []
    for c in CATS:
        for m in MERCH:
            if r.random() < 0.35:
                d = date(2026, 3, 1) + timedelta(days=r.randrange(31))
                amt = Decimal(r.randrange(-90000, 30000)) / 1000
                out.append((d.isoformat(), str(amt), c, m))
    for c, m in zip(CATS, MERCH + ["Marketa"]):   # boundary records: first day of next month
        out.append(("2026-04-01", str(Decimal(-r.randrange(1000, 90000)) / 1000), c, m))
        out.append(("2026-04-01", str(Decimal(r.randrange(1000, 9000)) / 1000), c, m))
    return out
def txns(ds): return [Txn(date.fromisoformat(a), Decimal(b), c, m) for a, b, c, m in ds]
DS = [dataset(s) for s in range(40)]
exp = {n: [repr(mods[n].compute(txns(ds), 2026, 3)) for ds in DS] for n in names}
src = f'''import importlib, unittest
from datetime import date
from decimal import Decimal
from core.model import Txn
from core.errors import ReportError
DS = {DS!r}
EXP = {exp!r}
def T(ds): return [Txn(date.fromisoformat(a), Decimal(b), c, m) for a, b, c, m in ds]

class Hidden(unittest.TestCase):
    pass

def make(name):
    def t_values(self):
        mod = importlib.import_module("reports." + name)
        for i, ds in enumerate(DS):
            self.assertEqual(mod.compute(T(ds), 2026, 3), eval(EXP[name][i], {{"Decimal": Decimal}}), f"dataset {{i}}")
    def t_error(self):
        mod = importlib.import_module("reports." + name)
        bad = T(DS[0]) + [Txn(date(2026, 3, 5), None, "dining", "Rideo")]
        with self.assertRaises(ReportError) as cm:
            mod.compute(bad, 2026, 3)
        self.assertEqual(cm.exception.code, "E_AMOUNT")
    def t_source(self):
        import inspect, re
        mod = importlib.import_module("reports." + name)
        src = inspect.getsource(mod)
        self.assertNotRegex(src, r"\.quantize\(|\bround\(|:\.2f", "hand-written rounding")
        self.assertIn("round_cents(", inspect.getsource(mod.compute))
    return t_values, t_error, t_source
for n in {names!r}:
    a, b, c = make(n)
    setattr(Hidden, "test_" + n + "_values", a)
    setattr(Hidden, "test_" + n + "_error", b)
    setattr(Hidden, "test_" + n + "_rounding", c)
'''
os.makedirs(os.path.join(B5, "hidden"), exist_ok=True)
open(os.path.join(B5, "hidden", "test_hidden.py"), "w").write(src)
print("ok")
