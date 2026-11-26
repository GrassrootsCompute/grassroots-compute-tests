# 草根算力 第 1 期：本地大模型 vs 云端 Claude Sonnet 4.6，五轮编程实测

视频：https://youtu.be/re4owP9mNcY

这个仓库放第一期视频里用到的全部题目、隐藏测试、打分脚本，以及两边模型最终交出的代码，方便你自己复跑、挑错。

## 测了什么

同一套 Claude Code 命令行（`claude -p`，相同的权限和提示词），一边接本地模型，一边接云端 Claude Sonnet 4.6，让它们在真实的小项目里改代码，用**藏起来的测试**打分。

| 轮 | 目录 | 题目 |
|---|---|---|
| 1 | `round1-single-tasks` | 单题：测速（问答 / 写代码 / 8 千 token 长文总结）；修一个购物车模块里的 5 处 bug（6 个测试，不许改测试） |
| 2 | `round2-checkout-spec` | 照说明书写结账函数（折扣码、买一送一、运费、税、四舍五入），给看 4 个测试，藏 10 个 |
| 3 | `round3-multi-step-ledger` | 4 个文件的记账命令行工具，连续三轮需求（`--resume` 接着上一轮会话）：加分类；加多币种和取整；修月底边界 bug 并加 CSV 导出。每轮把前几轮的隐藏测试一起跑，看有没有改坏 |
| 4 | `round4-open-ended` | 开放题：「用户说月底才知道自己超支了，你自己决定怎么改」。没有标准答案，看它选了什么、为什么 |
| 5 | `round5-long-audit` | 超出 64K 上下文的长任务：120 个报表模块，12 个各违反一条规范（四舍五入 / 月底多算一天 / 报错方式），要求逐个找出并修好，不许动合规的模块。每个模块 40 组数据 + 坏数据检查 |

## 硬件和模型

- 机器：家用 PC，RTX 3080 Ti（12 GB 显存），32 GB 内存。
- 本地：Qwen3.8-Flash-Next（125B MoE，每次动用约 6B），Q2_0 量化，跑在 Strata 里，上下文 64K。
- 云端：Claude Sonnet 4.6（`claude-sonnet-4-6`）。
- 对照：Ollama 上的 `qwen3.8:27b`（稠密 27B，q4，上下文 64K），只测了结账题。

## 结果总表

| 轮 | Sonnet 4.6 | 本地 Q2_0 |
|---|---|---|
| 1 修 5 处 bug | 64 秒、9 轮，全对 | 189 秒、10 轮，全对 |
| 2 结账函数（藏 10 个测试） | 71 秒、7 轮，10/10 | 356 秒、18 轮，10/10 |
| 3 连续三轮（隐藏 14 个测试） | 150+177+139 = 466 秒，17+12+8 轮；三轮全对，没改坏；自己写了 41 个测试 | 314+330+292 = 936 秒，21+15+15 轮；三轮全对，没改坏；自己写了 28 个测试 |
| 4 开放题 | 282 秒、13 轮 | 696 秒、19 轮 |
| 5 长任务（12 处违规） | 7 / 8 / 4（147 / 210 / 137 秒），均无误伤 | 12 / 12 / 8（1,460 / 1,287 / 851 秒），均无误伤 |

补充：
- 速度（本地，第 1 轮 `speed_results.json`）：短问答约 40 token/秒，写代码约 31，8 千 token 长文总结约 30（读完要 16 秒才出第一个字）。
- Ollama `qwen3.8:27b`：63% 在 CPU、37% 在显卡；单独问答生成 9.4 token/秒，接进 Claude Code 做结账题只有 3.2 token/秒，40 分钟限时到了一个文件都没写出来。同一道题本地 Strata 用了 6 分钟左右做完。
- 第 4 轮两边都选了「预算 + 按当前速度预测月底花费」；两边有同一个毛病：有外币交易又没给汇率时直接打出 Python 报错堆栈。
- 第 5 轮 Sonnet 三次都靠搜关键字找，漏得最多的是日期写法不统一的几处和字符串格式化取整。本地一次跑了自己写的语法树扫描加运行时探测，把 120 个模块逐个跑了一遍。

各轮 `results.json` 是从原始运行记录里抽出来的用时、轮数、通过数（不含原始会话记录）。

## 怎么复现

需要 Python 3（只用标准库）。每个 `roundN-*/grade.py` 对一份代码打分：

```bash
cd ep01-local-vs-cloud
python3 round1-single-tasks/grade.py solutions/local-bugfix      # 6 个测试
python3 round2-checkout-spec/grade.py solutions/sonnet           # 10 个隐藏测试
python3 round3-multi-step-ledger/grade.py solutions/local        # 三套隐藏测试
python3 round4-open-ended/grade.py solutions/sonnet              # 只跑模型自己写的测试
python3 round5-long-audit/grade.py solutions/local3              # 12 处违规修了几处
```

生成器：
- 第 5 轮题目由 `round5-long-audit/gen.py <输出目录>` 生成（固定随机种子），隐藏测试由 `mkhidden.py <第5轮目录>` 以参考答案 `ref/` 为准生成。
- 想让你自己的模型来做：把 `claude -p` 指向你的模型，提示词在各轮的 `prompt.txt` / `prompts.txt`，原始跑法见各轮 `run.sh`（里面的 `ANTHROPIC_AUTH_TOKEN=strata-local` 只是本地服务要求填的占位值，不是密钥）。`run.sh` 是当时的原始脚本，目录布局以它里面的名字为准（第 3 轮的 `base/`、第 5 轮的 `task/`、`ref/`、`hidden/`），其中第 3、4 轮 `run.sh` 里的 `start`/`base` 目录名对应本仓库同名目录。

## 已知问题和局限

- **样本很少**：每道题多数只跑了一次（第 5 轮 Sonnet 三次、本地三次）。差别在误差范围内的地方别当结论。
- 单次运行，没有固定随机种子；换一次可能得到不同结果（第 5 轮本地 12 / 12 / 8 就是例子）。
- 题目都是小到中等的 Python 项目，由我们自己出，不代表真实大型项目。
- 第 3 轮隐藏测试里 h2、h3 在对应功能还没做之前会失败，这是预期，只有第 3 步之后的结果有意义。
- Ollama 对照只测了结账题，且受 12 GB 显存限制，大部分在 CPU 上跑；不能代表该模型在更大显存上的表现。
- 第 2 轮的 Ollama 失败产物没有放进仓库（没有写出任何文件）。
- 第 1 轮的长文总结用的是一份内部文档，未公开；`speed_bench.py` 的第一个参数换成任意一篇约 1 万字的文本即可，数字只具参考意义。
- 第 3、4、5 轮的 `run.sh` 里 Sonnet 一侧用的是你自己登录的账号，仓库不含任何账号配置。
- 个人实测记录，**不构成任何购买建议**。

## License

MIT，见 `LICENSE`。

---

## English summary

This repository contains the tasks, hidden tests, grading scripts and final model-written code from episode 1 of the "Grassroots Compute" YouTube channel: a local Qwen3.8-Flash-Next (Q2_0, run with Strata, 64K context) versus Claude Sonnet 4.6, both driven through the same Claude Code CLI, on a home PC with an RTX 3080 Ti (12 GB VRAM) and 32 GB RAM. Ollama `qwen3.8:27b` was included as a comparison on one task.

Five rounds: (1) single tasks (speed, fix 5 bugs), (2) implement a checkout function from a spec (10 hidden tests), (3) three consecutive feature requests on a small ledger CLI (hidden tests re-run each step), (4) an open-ended "help users notice overspending" task, (5) a long audit of 120 report modules exceeding the 64K context (12 planted violations; Sonnet fixed 7/8/4, the local model 12/12/8, none broke compliant modules). Local runs were roughly 2-5x slower on the small tasks. See the table above and each `results.json`. Run `python3 roundN-*/grade.py <solution-dir>` to re-grade. Caveats: very few runs per task, self-made tasks, single-run noise. Personal test notes, not purchase advice. Video: https://youtu.be/re4owP9mNcY
