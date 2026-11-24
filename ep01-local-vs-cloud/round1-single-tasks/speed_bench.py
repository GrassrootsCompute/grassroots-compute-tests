import json, time, urllib.request, sys
URL = "http://127.0.0.1:18080/v1/chat/completions"
doc = open(sys.argv[1], encoding="utf-8").read()[:14000]
tests = [
 ("chat", "用中文简要解释：为什么 MoE 模型总参数很大、但每次推理只用一小部分参数也能保持效果？三段以内。"),
 ("code", "Write a Python function `merge_intervals(xs)` that takes a list of [start, end] integer pairs (possibly unsorted, possibly touching like [1,2],[2,3]) and returns the merged list sorted by start; touching intervals must merge. Then write 5 assert-based tests. Output only one ```python code block."),
 ("summary", "下面是一份内部手册的片段。请用中文列出其中最重要的 6 条硬规则，每条一句话，不要编造原文没有的内容。\n\n" + doc),
]
res = {}
for name, prompt in tests:
    body = json.dumps({"model": "q", "messages": [{"role": "user", "content": prompt}], "max_tokens": 1500, "stream": True, "stream_options": {"include_usage": True}}).encode()
    req = urllib.request.Request(URL, body, {"Content-Type": "application/json"})
    t0 = time.time(); first = None; text = ""; usage = None; nchunks = 0
    with urllib.request.urlopen(req, timeout=900) as r:
        for line in r:
            line = line.decode().strip()
            if not line.startswith("data:"): continue
            d = line[5:].strip()
            if d == "[DONE]": break
            j = json.loads(d)
            if j.get("usage"): usage = j["usage"]
            for c in j.get("choices", []):
                delta = c.get("delta", {})
                piece = (delta.get("content") or "") + (delta.get("reasoning_content") or "")
                if piece:
                    if first is None: first = time.time()
                    text += delta.get("content") or ""; nchunks += 1
    t1 = time.time()
    ct = (usage or {}).get("completion_tokens", nchunks); pt = (usage or {}).get("prompt_tokens")
    res[name] = dict(prompt_tokens=pt, completion_tokens=ct, ttft=round(first - t0, 2) if first else None, total=round(t1 - t0, 1), decode_tps=round(ct / (t1 - first), 1) if first and t1 > first else None)
    open(f"{sys.argv[2]}/out-{name}.txt", "w").write(text)
    print(name, res[name], flush=True)
json.dump(res, open(f"{sys.argv[2]}/bench.json", "w"), ensure_ascii=False, indent=1)
