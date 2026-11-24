"""Round 1: run the visible tests of a bug-fix solution directory.
usage: python3 grade.py [bugfix_start | solutions/local-bugfix | solutions/sonnet-bugfix]
(bugfix_start is the buggy starting code: expect 5 failures out of 6.)"""
import subprocess, sys, os
d = os.path.join(os.path.dirname(os.path.abspath(__file__)), sys.argv[1] if len(sys.argv) > 1 else "solutions/local-bugfix")
r = subprocess.run([sys.executable, "-m", "unittest"], cwd=d, capture_output=True, text=True)
print(d.split(os.sep)[-1], "->", r.stderr.strip().splitlines()[-1])
