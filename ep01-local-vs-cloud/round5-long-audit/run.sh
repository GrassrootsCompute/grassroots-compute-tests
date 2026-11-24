#!/bin/bash
B5=$(cd "$(dirname "$0")" && pwd); MODE=$1; W=$B5/$MODE; rm -rf $W $W.cfg; cp -r $B5/task $W; mkdir -p $W.cfg; cd $W
if [[ "$MODE" == local* ]]; then
  ENVS=(env -u ANTHROPIC_API_KEY CLAUDE_CONFIG_DIR=$W.cfg ANTHROPIC_BASE_URL=http://127.0.0.1:18080 ANTHROPIC_AUTH_TOKEN=strata-local ANTHROPIC_MODEL=qwen3.8-flash-next-q2_0 ANTHROPIC_SMALL_FAST_MODEL=qwen3.8-flash-next-q2_0 ANTHROPIC_DEFAULT_SONNET_MODEL=qwen3.8-flash-next-q2_0 ANTHROPIC_DEFAULT_OPUS_MODEL=qwen3.8-flash-next-q2_0 ANTHROPIC_DEFAULT_HAIKU_MODEL=qwen3.8-flash-next-q2_0 CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1 DISABLE_AUTOUPDATER=1 DISABLE_TELEMETRY=1 CLAUDE_CODE_MAX_CONTEXT_TOKENS=65536 CLAUDE_CODE_MAX_OUTPUT_TOKENS=8192); MODEL=()
else ENVS=(env -u ANTHROPIC_BASE_URL); MODEL=(--model claude-sonnet-4-6); fi
t0=$(date +%s)
"${ENVS[@]}" timeout 5400 claude -p "$(cat $B5/prompt.txt)" "${MODEL[@]}" --permission-mode acceptEdits --allowedTools "Read" "Edit" "Write" "Glob" "Grep" "Bash(python3 *)" "Bash(grep *)" "Bash(ls *)" "Bash(wc *)" --output-format json > $B5/$MODE.json 2> $B5/$MODE.err
rc=$?; secs=$(( $(date +%s)-t0 ))
G=$(mktemp -d); cp -r $W/. $G/; cp $B5/hidden/test_hidden.py $G/tests/
FAILS=$(cd $G && python3 -m unittest tests.test_hidden 2>&1 | grep -E "^(FAIL|ERROR):" | sed -E 's/^(FAIL|ERROR): test_(r[0-9]+_[a-z_]+)_(values|error|rounding).*/\2/' | sort -u | tr '\n' ' '); rm -rf $G
python3 - "$B5" "$MODE" "$rc" "$secs" "$FAILS" <<'PY'
import json,sys
B5,mode,rc,secs,fails=sys.argv[1:]
ans=set(json.load(open(f"{B5}/answer.json"))["violations"]); fails=set(fails.split())
try: d=json.load(open(f"{B5}/{mode}.json"))
except Exception: d={}
out=dict(mode=mode,rc=int(rc),secs=int(secs),turns=d.get("num_turns"),is_error=d.get("is_error"),
 fixed=sorted(ans-fails),missed=sorted(ans&fails),broke=sorted(fails-ans),cost=d.get("total_cost_usd"))
json.dump(out,open(f"{B5}/{mode}.score.json","w"),indent=1); print(json.dumps(out,ensure_ascii=False))
PY
