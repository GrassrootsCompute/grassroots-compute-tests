"""Round 3: run the three hidden suites (h1 category, h2 currency, h3 bug+export) against a final solution.
usage: python3 grade.py [solutions/local | solutions/sonnet | reference]  (reference holds only ledger/; tests are the hidden ones)"""
import subprocess, sys, os, shutil, tempfile, glob
here = os.path.dirname(os.path.abspath(__file__))
rel = sys.argv[1] if len(sys.argv) > 1 else "solutions/local"
src = os.path.join(here, rel)
for f in sorted(glob.glob(os.path.join(here, "hidden", "test_h*.py"))):
    with tempfile.TemporaryDirectory() as t:
        shutil.copytree(os.path.join(src, "ledger"), os.path.join(t, "ledger"))
        os.makedirs(os.path.join(t, "tests")); open(os.path.join(t, "tests", "__init__.py"), "w").close()
        shutil.copy(os.path.join(here, "hidden", "_common.py"), os.path.join(t, "tests", "_common_hidden.py"))
        shutil.copy(f, os.path.join(t, "tests"))
        m = os.path.basename(f)[:-3]
        r = subprocess.run([sys.executable, "-m", "unittest", "tests." + m], cwd=t, capture_output=True, text=True)
        print(rel, m, "->", " ".join(r.stderr.strip().splitlines()[-2:]))
