import json, os, subprocess, sys, tempfile
def cli(path, *args):
    r = subprocess.run([sys.executable, "-m", "ledger.cli", "--file", path, *args], capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise AssertionError(f"cli failed rc={r.returncode}: {r.stderr[-500:]}")
    return r.stdout
