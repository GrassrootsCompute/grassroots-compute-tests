"""第二期考试脚本：三位考生同一套题，实时一行一题滚动（方便录屏），结果写 results/<run>.jsonl。

考生：
  ds9b    蒸馏版 DeepSeek-V4-Pro-Qwen3.5-9B（Q4_K_M，PC 上 Ollama）
  qwen9b  原版 Qwen3.5-9B（Q4_K_M，PC 上 Ollama）
  teacher 老师 DeepSeek-V4-Pro（官方 API，密钥读 ~/.config/deepseek/key，不打印）
Ollama 走 ssh 隧道：先 `ssh -N -L 11434:127.0.0.1:11434 pc`（本脚本 --tunnel 会自动开）。

用法：
  python3 run_exam.py --who ds9b,qwen9b,teacher --runs 3 [--only M01,C02] [--tunnel] [--tag 正式]
"""
import argparse, json, os, re, shutil, subprocess, sys, tempfile, time, urllib.request
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
NAMES = {"ds9b": "蒸馏版 9B", "qwen9b": "原版 9B", "teacher": "老师 V4-Pro", "strata": "本地 3.8 Flash"}
STRATA = "http://127.0.0.1:18080/v1/chat/completions"  # PC 上 Strata（Qwen3.8-Flash-Next 125B MoE），经 ssh -L 18080 隧道
OLLAMA = "http://127.0.0.1:11434/api/chat"
DS_URL = "https://api.deepseek.com/chat/completions"
G, R, Y, D, B, X = "\033[32m", "\033[31m", "\033[33m", "\033[2m", "\033[1m", "\033[0m"


def post(url, body, headers=None, timeout=1800):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode(), strict=False)


def ask_strata(prompt, t0):
    """Strata 是 OpenAI 格式，流式；思考在 delta.reasoning_content（没有就当正文）。"""
    body = {"model": "q2_0", "stream": True, "max_tokens": 30000, "temperature": 0.6, "top_p": 0.95,
            "messages": [{"role": "user", "content": prompt}], "stream_options": {"include_usage": True}}
    req = urllib.request.Request(STRATA, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    th, an, usage, mode, first = [], [], {}, None, None
    with urllib.request.urlopen(req, timeout=3600) as r:
        for line in r:
            line = line.decode("utf-8", "replace").strip()
            if not line.startswith("data:"): continue
            data = line[5:].strip()
            if data == "[DONE]": break
            d = json.loads(data, strict=False)
            if d.get("usage"): usage = d["usage"]
            for ch in d.get("choices") or []:
                dl = ch.get("delta") or {}
                t, c = dl.get("reasoning_content") or "", dl.get("content") or ""
                if (t or c) and first is None: first = time.time()
                if t:
                    if mode != "t": live(f"{D}"); mode = "t"
                    th.append(t); live(t)
                if c:
                    if mode != "c": live(f"{X}\n{B}── 作答 ──{X}\n"); mode = "c"
                    an.append(c); live(c)
    live(f"{X}\n")
    ans = "".join(an)
    if "</think>" in ans: th.append(ans.split("</think>")[0]); ans = ans.split("</think>")[-1]
    ev = usage.get("completion_tokens") or 0
    gen = time.time() - (first or t0)
    return {"answer": ans, "thinking": "".join(th), "out_tokens": ev,
            "secs": round(time.time() - t0, 1), "tps": round(ev / gen, 1) if ev and gen > 0 else None}


def ask(who, prompt):
    t0 = time.time()
    if who == "strata":
        return ask_strata(prompt, t0)
    if who == "teacher":
        key = open(os.path.expanduser("~/.config/deepseek/key")).read().strip()
        d = post(DS_URL, {"model": "deepseek-v4-pro", "messages": [{"role": "user", "content": prompt}], "max_tokens": 32000},
                 {"Authorization": f"Bearer {key}"})
        m = d["choices"][0]["message"]; u = d.get("usage", {})
        return {"answer": m.get("content") or "", "thinking": m.get("reasoning_content") or "",
                "out_tokens": u.get("completion_tokens"), "secs": round(time.time() - t0, 1), "tps": None}
    body = {"model": who, "stream": True, "messages": [{"role": "user", "content": prompt}],
            "options": {"temperature": 0.6, "top_p": 0.95, "top_k": 20, "num_ctx": 36864, "num_predict": 30000}}
    req = urllib.request.Request(OLLAMA, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    th, an, last, mode = [], [], {}, None
    with urllib.request.urlopen(req, timeout=1800) as r:
        for line in r:
            if not line.strip(): continue
            d = json.loads(line.decode(), strict=False); m = d.get("message") or {}
            t, c = m.get("thinking") or "", m.get("content") or ""
            if t:
                if mode != "t": live(f"{D}"); mode = "t"
                th.append(t); live(t)
            if c:
                if mode != "c": live(f"{X}\n{B}── 作答 ──{X}\n"); mode = "c"
                an.append(c); live(c)
            if d.get("done"): last = d
    live(f"{X}\n")
    ev = last.get("eval_count") or 0; dur = (last.get("eval_duration") or 1) / 1e9
    return {"answer": "".join(an), "thinking": "".join(th), "out_tokens": ev,
            "secs": round(time.time() - t0, 1), "tps": round(ev / dur, 1) if ev else None}


LIVE = None
def live(s):
    if LIVE: LIVE.write(s); LIVE.flush()


def num(s):
    s = s.strip().replace("，", ",").replace(",", "").replace(" ", "").rstrip("。.").replace("−", "-")
    s = re.sub(r"[^\d\-./%]+$", "", s)            # 去掉单位尾巴
    m = re.search(r"-?\d+(?:\.\d+)?(?:/\d+)?%?", s)
    if not m: return None
    t = m.group(0); pct = t.endswith("%"); t = t.rstrip("%")
    try:
        v = Fraction(t)
    except Exception:
        return None
    return v / 100 if pct else v


def grade_text(q, a, out):
    lines = [l for l in out.strip().splitlines() if l.strip()]
    tail = next((l for l in reversed(lines) if "答案" in l), lines[-1] if lines else "")
    got = tail.split("答案", 1)[-1].lstrip("：: ") if "答案" in tail else tail
    gv, av = num(got), num(str(a["answer"]))
    if gv is None or av is None:
        return False, got[:40]
    tol = Fraction(1, 10 ** int(a["places"])) / 2 if "places" in a else Fraction(1, 10 ** 6) * max(1, abs(av))
    return abs(gv - av) <= tol, got[:40]


def grade_code(q, out):
    code = re.findall(r"```(?:python)?\n(.*?)```", out, re.S)
    code = max(code, key=len) if code else out
    tmp = tempfile.mkdtemp(prefix="exam-")
    try:
        open(os.path.join(tmp, "solution.py"), "w").write(code)
        shutil.copy(os.path.join(HERE, "coding", f"test_{q['id']}.py"), tmp)
        p = subprocess.run([sys.executable, "-m", "unittest", "-q", f"test_{q['id']}"], cwd=tmp, capture_output=True, text=True, timeout=60)
        m = re.search(r"Ran (\d+) test", p.stderr); n = int(m.group(1)) if m else 0
        f = re.search(r"failures=(\d+)", p.stderr); e = re.search(r"errors=(\d+)", p.stderr)
        bad = (int(f.group(1)) if f else 0) + (int(e.group(1)) if e else 0)
        if n == 0: bad = 1
        return bad == 0, ("测试全过" if bad == 0 else f"{bad} 处没过")
    except subprocess.TimeoutExpired:
        return False, "超时"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    import signal; signal.signal(signal.SIGTERM, lambda *a: sys.exit(143))
    ap = argparse.ArgumentParser()
    ap.add_argument("--who", default="ds9b,qwen9b,teacher"); ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--only", default=""); ap.add_argument("--tunnel", action="store_true"); ap.add_argument("--tag", default=""); ap.add_argument("--suffix", default="", help="追加在每道题后面的话，比如缩进提示")
    a = ap.parse_args()
    Q = json.load(open(os.path.join(HERE, "questions.json"))); A = json.load(open(os.path.join(HERE, "answers.json")))
    if isinstance(Q, dict): Q = Q.get("questions", Q)
    if a.only: Q = [q for q in Q if q["id"] in a.only.split(",")]
    tun = None
    if a.tunnel:
        tun = subprocess.Popen(["ssh", "-N", "-o", "ExitOnForwardFailure=yes", "-o", "ServerAliveInterval=15", "-L", "11434:127.0.0.1:11434", "-L", "18080:127.0.0.1:8080", os.environ.get("PC_HOST", "pc-wifi")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(3)
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    out_path = os.path.join(HERE, "results", time.strftime("%m%d-%H%M") + (f"-{a.tag}" if a.tag else "") + ".jsonl")
    score = {}
    global LIVE
    LIVE = open(os.path.join(HERE, "results", "live.txt"), "a")
    print(f"{B}第二期考试 · {len(Q)} 道题 × {a.runs} 次 · 考生：{' / '.join(NAMES[w] for w in a.who.split(','))}{X}\n")
    try:
        with open(out_path, "w") as f:
            for q in Q:
                for w in a.who.split(","):
                    for r in range(a.runs):
                        live(f"\n\n{B}{Y}━━ [{q['id']}] {NAMES[w]} · 第 {r + 1} 次 ━━{X}\n{q['question'][:160]}\n\n")
                        try:
                            res = ask(w, q["question"] + (("\n\n" + a.suffix) if a.suffix else ""))
                        except Exception as e:
                            res = {"answer": "", "thinking": "", "out_tokens": None, "secs": None, "tps": None, "error": str(e)[:200]}
                        ok, got = (grade_code(q, res["answer"]) if q["id"].startswith("C") else grade_text(q, A[q["id"]], res["answer"]))
                        s = score.setdefault(w, {"ok": 0, "n": 0, "tok": 0}); s["ok"] += ok; s["n"] += 1; s["tok"] += res.get("out_tokens") or 0
                        mark = f"{G}✓{X}" if ok else f"{R}✗{X}"
                        print(f"[{q['id']}] {NAMES[w]:<8} {mark}  答：{got:<14} {D}输出 {res.get('out_tokens') or '-':>5} token · {res.get('secs') or '-':>6}s{(' · %s tok/s' % res['tps']) if res.get('tps') else ''}{X}", flush=True)
                        f.write(json.dumps({"id": q["id"], "who": w, "run": r, "ok": ok, "got": got, **res}, ensure_ascii=False) + "\n"); f.flush()
                print()
        print(f"{B}总分{X}")
        for w, s in score.items():
            print(f"  {NAMES[w]:<8} {s['ok']}/{s['n']} = {100 * s['ok'] / max(s['n'], 1):.0f}%   平均输出 {s['tok'] // max(s['n'], 1)} token")
        print(f"\n{D}结果：{os.path.relpath(out_path, HERE)}{X}")
    finally:
        if tun: tun.terminate()


if __name__ == "__main__":
    main()
