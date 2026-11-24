"""Round 2: run the 10 hidden tests against a solution.
usage: python3 grade.py [solutions/local | solutions/sonnet | reference]"""
import subprocess, sys, os, shutil, tempfile
here = os.path.dirname(os.path.abspath(__file__))
src = os.path.join(here, sys.argv[1] if len(sys.argv) > 1 else "solutions/local")
with tempfile.TemporaryDirectory() as t:
    shutil.copytree(os.path.join(src, "shop"), os.path.join(t, "shop"))
    os.makedirs(os.path.join(t, "tests"))
    open(os.path.join(t, "tests", "__init__.py"), "w").close()
    shutil.copy(os.path.join(here, "hidden", "test_hidden.py"), os.path.join(t, "tests"))
    r = subprocess.run([sys.executable, "-m", "unittest", "tests.test_hidden"], cwd=t, capture_output=True, text=True)
print(sys.argv[1] if len(sys.argv) > 1 else "solutions/local", "->", " ".join(r.stderr.strip().splitlines()[-3:]))
