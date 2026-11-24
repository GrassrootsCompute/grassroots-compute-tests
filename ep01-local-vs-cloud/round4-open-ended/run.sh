#!/bin/bash
O=$(cd "$(dirname "$0")" && pwd); MODE=$1; W=$O/$MODE; rm -rf $W $W.cfg; cp -r $O/start $W; mkdir -p $W.cfg; cd $W
if [ "$MODE" = local ]; then
  ENVS=(env -u ANTHROPIC_API_KEY CLAUDE_CONFIG_DIR=$W.cfg ANTHROPIC_BASE_URL=http://127.0.0.1:18080 ANTHROPIC_AUTH_TOKEN=strata-local ANTHROPIC_MODEL=qwen3.8-flash-next-q2_0 ANTHROPIC_SMALL_FAST_MODEL=qwen3.8-flash-next-q2_0 ANTHROPIC_DEFAULT_SONNET_MODEL=qwen3.8-flash-next-q2_0 ANTHROPIC_DEFAULT_OPUS_MODEL=qwen3.8-flash-next-q2_0 ANTHROPIC_DEFAULT_HAIKU_MODEL=qwen3.8-flash-next-q2_0 CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1 DISABLE_AUTOUPDATER=1 DISABLE_TELEMETRY=1 CLAUDE_CODE_MAX_CONTEXT_TOKENS=65536 CLAUDE_CODE_MAX_OUTPUT_TOKENS=8192); MODEL=()
else ENVS=(env -u ANTHROPIC_BASE_URL); MODEL=(--model claude-sonnet-4-6); fi
t0=$(date +%s)
"${ENVS[@]}" timeout 2400 claude -p "$(cat $O/prompt.txt)" "${MODEL[@]}" --permission-mode acceptEdits --allowedTools "Read" "Edit" "Write" "Glob" "Grep" "Bash(python3 *)" --output-format json > $O/$MODE.json 2> $O/$MODE.err
echo "$MODE rc=$? secs=$(( $(date +%s)-t0 ))"; python3 -c "import json;d=json.load(open('$O/$MODE.json'));print('turns',d.get('num_turns'))"
cd $W && python3 -m unittest 2>&1 | grep -E "^(Ran|OK|FAILED)"
