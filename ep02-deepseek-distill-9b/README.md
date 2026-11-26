# 第二期：DeepSeek 蒸馏版 9B 实测（Episode 2: DeepSeek-V4-Pro distilled 9B）

视频：https://youtu.be/zivxjL26IcA

36 道新出的题（数学 20、理科 10、编程 6），四位考生：

| 考生 | 怎么跑 |
|---|---|
| 蒸馏版 9B：Jackrong/DeepSeek-V4-Pro-Qwen3.5-9B（MTP GGUF，Q4_K_M） | Ollama，RTX 3080 Ti 12G，每题 3 遍 |
| 原版 Qwen3.5-9B（unsloth GGUF，Q4_K_M） | Ollama，同一张卡，每题 3 遍 |
| 本地 3.8 Flash（125B MoE，Q2_0） | Strata，同一张卡，每题 1 遍 |
| 老师 DeepSeek-V4-Pro | 官方 API，每题 1 遍 |

参数：temperature 0.6、top_p 0.95、top_k 20，单题输出上限 30000 token。

## 成绩

| | 总分 | 数学 | 理科 | 编程 | 平均输出 token |
|---|---|---|---|---|---|
| 老师 DeepSeek-V4-Pro | 97% | 95% | 100% | 100% | 5303 |
| 本地 3.8 Flash | 89% | 85% | 90% | 100% | 2458 |
| 原版 Qwen3.5-9B | 81% | 80% | 93% | 61% | 11846 |
| 蒸馏版 9B | 71% | 83% | 90% | 0% | 6008 |

补考：每道编程题末尾加一句「注意：代码请用标准的 4 个空格缩进。」，蒸馏版重考 6 题 × 3 遍，结果还是 0/18。

## 文件
- `questions.json`、`answers.json`：题目和标准答案；`verify.py` 用参考解核对答案。
- `coding/`：`ref_Cxx.py` 是参考解，`test_Cxx.py` 是隐藏测试（考试时模型看不到）。
- `run_exam.py`：考试和判分脚本。数学、理科只认最后一行「答案：」，按小数位比对；编程题把最长的代码块存成 solution.py，跑隐藏测试，全部通过才算对。
- `results/*.jsonl`：每次作答一行，包括完整的思考、答案、输出 token 数、用时、速度。

## 说明
- 速度：有 8 条作答在测试期间被同一张显卡上的其他任务拖慢了（tps < 100），算速度时已剔除，对错不受影响。这 8 条是：C02 原版 ×3、C04 原版 ×3、C04 蒸馏版 ×1、C05 蒸馏版 ×1。
- C05、C06 因为网络断线，两个 9B 重考了一次，结果在 `*students-rerun-C05-C06.jsonl`，以它为准；`*students.jsonl` 里 C05 蒸馏版的第一条作废。
- 蒸馏版编程 0 分的原因：它在对话里写的代码一律只用 1 个空格缩进，Python 报 IndentationError。我们翻遍了它全部约 147 万字符的输出，连续两个空格出现 0 次。但用 raw 续写模式时，它能写出 4 个空格。
- 个人实测记录，不构成任何购买或投资建议。

---

English summary: 36 fresh questions (20 math, 10 science, 6 coding with hidden unit tests). The distilled 9B scored 71% overall, 83% on math (above the original's 80%), and 0% on coding, because every code block it writes in chat mode uses 1-space indentation (zero double spaces in ~1.47M characters of output). It still fails after we explicitly ask for 4-space indentation. The teacher scored 97%, and the local 125B MoE model (Strata, RTX 3080 Ti) scored 89%.
