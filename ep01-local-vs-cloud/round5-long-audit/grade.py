"""Round 5: how many of the 12 planted violations did a solution fix? (hidden tests, 40 datasets per module)
usage: python3 grade.py [solutions/local | solutions/sonnet2 | ref | task ...]"""
import subprocess, sys, os, shutil, tempfile, re, json
here = os.path.dirname(os.path.abspath(__file__))
rel = sys.argv[1] if len(sys.argv) > 1 else "solutions/local"
planted = set(json.load(open(os.path.join(here, "answer.json")))["violations"])
with tempfile.TemporaryDirectory() as t:
    shutil.copytree(os.path.join(here, rel), t, dirs_exist_ok=True)
    os.makedirs(os.path.join(t, "tests"), exist_ok=True)
    shutil.copy(os.path.join(here, "hidden", "test_hidden.py"), os.path.join(t, "tests"))
    r = subprocess.run([sys.executable, "-m", "unittest", "tests.test_hidden"], cwd=t, capture_output=True, text=True)
failed = set(re.findall(r"^(?:FAIL|ERROR): test_(r\d+_[a-z_]+?)_(?:values|error|rounding)", r.stderr, re.M))
print(rel, "->", len(planted - failed), "/ 12 fixed; missed:", sorted(planted & failed), "; broke compliant:", sorted(failed - planted))
