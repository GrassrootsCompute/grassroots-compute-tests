#!/bin/bash
# usage: run.sh sonnet|local   → $B3/<mode>/ work dir + results.jsonl
B3=$(cd "$(dirname "$0")" && pwd); MODE=$1; W=$B3/$MODE; rm -rf $W $W.cfg $B3/$MODE.results.jsonl; cp -r $B3/base $W; mkdir -p $W.cfg
if [ "$MODE" = local ]; then
  ENVS=(env -u ANTHROPIC_API_KEY CLAUDE_CONFIG_DIR=$W.cfg ANTHROPIC_BASE_URL=http://127.0.0.1:18080 ANTHROPIC_AUTH_TOKEN=strata-local ANTHROPIC_MODEL=qwen3.8-flash-next-q2_0 ANTHROPIC_SMALL_FAST_MODEL=qwen3.8-flash-next-q2_0 ANTHROPIC_DEFAULT_SONNET_MODEL=qwen3.8-flash-next-q2_0 ANTHROPIC_DEFAULT_OPUS_MODEL=qwen3.8-flash-next-q2_0 ANTHROPIC_DEFAULT_HAIKU_MODEL=qwen3.8-flash-next-q2_0 CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1 DISABLE_AUTOUPDATER=1 DISABLE_TELEMETRY=1 CLAUDE_CODE_MAX_CONTEXT_TOKENS=65536 CLAUDE_CODE_MAX_OUTPUT_TOKENS=8192)
  MODEL=()
else
  ENVS=(env -u ANTHROPIC_BASE_URL); MODEL=(--model claude-sonnet-4-6)
fi
SID=""; i=0
while IFS= read -r line; do
  [ -z "$line" ] && continue
  if [[ "$line" == STEP*"|||"* ]]; then i=$((i+1)); P[$i]="${line#*|||}"; else P[$i]+=$'\n'"$line"; fi
done < $B3/prompts.txt
for k in 1 2 3; do
  cd $W; t0=$(date +%s)
  RES=(); [ -n "$SID" ] && RES=(--resume "$SID")
  "${ENVS[@]}" timeout 2400 claude -p "${P[$k]}" "${MODEL[@]}" "${RES[@]}" --permission-mode acceptEdits --allowedTools "Read" "Edit" "Write" "Glob" "Grep" "Bash(python3 *)" --output-format json > $B3/$MODE.step$k.json 2> $B3/$MODE.step$k.err
  rc=$?; secs=$(( $(date +%s)-t0 ))
  SID=$(python3 -c "import json;print(json.load(open('$B3/$MODE.step$k.json')).get('session_id',''))" 2>/dev/null)
  G=$(mktemp -d); cp -r $W/. $G/; cp $B3/hidden/_common.py $G/tests/_common_hidden.py
  own=$(cd $W && python3 -m unittest 2>&1 | grep -E "^(Ran|OK|FAILED)" | tr '\n' ' ')
  hid=""; for h in 1 2 3; do f=$(ls $B3/hidden/test_h${h}_*.py); cp $f $G/tests/; m=$(basename $f .py)
    hid+="h$h:$(cd $G && python3 -m unittest tests.$m 2>&1 | grep -E '^(Ran|OK|FAILED)' | tr '\n' ' ')|"; done
  rm -rf $G
  python3 - "$B3/$MODE.step$k.json" "$MODE" "$k" "$rc" "$secs" "$own" "$hid" >> $B3/$MODE.results.jsonl <<'PY'
import json,sys
f,mode,k,rc,secs,own,hid=sys.argv[1:]
try: d=json.load(open(f))
except Exception: d={}
print(json.dumps(dict(mode=mode,step=int(k),rc=int(rc),secs=int(secs),turns=d.get('num_turns'),is_error=d.get('is_error'),cost=d.get('total_cost_usd'),own_tests=own.strip(),hidden=hid,result=(d.get('result') or '')[:600]),ensure_ascii=False))
PY
  tail -1 $B3/$MODE.results.jsonl | python3 -c "import json,sys;d=json.loads(sys.stdin.read());print(d['mode'],'step',d['step'],'rc',d['rc'],d['secs'],'s turns',d['turns'],'| own:',d['own_tests'],'| hidden:',d['hidden'])"
done
