"""Round 4 has no hidden tests: this only runs each solution's own tests.
usage: python3 grade.py [solutions/local | solutions/sonnet | start]"""
import subprocess, sys, os
d = os.path.join(os.path.dirname(os.path.abspath(__file__)), sys.argv[1] if len(sys.argv) > 1 else "solutions/local")
r = subprocess.run([sys.executable, "-m", "unittest"], cwd=d, capture_output=True, text=True)
print(sys.argv[1] if len(sys.argv) > 1 else "solutions/local", "->", " ".join(r.stderr.strip().splitlines()[-3:]))
