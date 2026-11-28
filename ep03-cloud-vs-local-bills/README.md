# 第三期：云端还是本地？三期实测的账单（Episode 3: cloud vs local, the bills）

视频：https://youtu.be/pdai3_77bJ8

这期没有出新题，是把前两期的实测和一个「AI 每小时模拟交易」实验的账单摊开来算：什么人该买显卡跑本地，什么人别买。视频里每个数字都能用 `python3 bills.py` 从 `data/` 复算出来。

## 结论用到的数字

| 视频里的说法 | 复算结果 | 出处 |
|---|---|---|
| 长任务 Claude Code 每跑一次 0.8–1.2 美元 | $1.03、$1.20、$0.83 | `data/round5-cost.json`（第 1 期第 5 轮） |
| Claude 两三分钟，本地 15–25 分钟 | 2.4 / 3.5 / 2.3 分钟；24.3 / 21.4 / 14.2 分钟 | 同上 |
| 本地一次电费约 2 美分（约 7 分钱） | 400 瓦 × 20 分钟 = 0.133 度 | 假设见下 |
| 专门买 5070 Ti，约 1500 次长任务回本（人民币版约 1800 次） | 1443 次；1758 次 | 假设见下 |
| Claude 每小时干一次活，平均每次约 3 美分 | $0.0326，输入约 5900、输出约 450 token | `data/trader-claude-usage.jsonl` |
| 按 4 周算一个月约 22 美元（约 150 元） | $21.9；¥146 | 同上 |
| 每次决策：Claude 约 5 秒，DeepSeek 一分多钟，本地小模型近 10 分钟 | 中位数 5.1 / 71.5 / 574 秒（59 轮） | `data/trader-decisions.jsonl` |
| 同一轮两段理由（见下） | 2026-11-26 11:20 UTC 那一轮 | 同上 |
| Ollama 跑 270 亿参数普通模型接 Claude Code，40 分钟一个文件没写出来 | 已在第 1 期公开 | `../ep01-local-vs-cloud/round2-checkout-spec/results.json` |
| 云端 97 分、旧显卡上的本地模型 89 分 | 已在第 2 期公开 | `../ep02-deepseek-distill-9b/` |

视频里引用的两段理由（2026-11-26 11:20 UTC，同一轮行情）：
- Claude：「大盘高位整理后短线回落，BTC卖盘较厚需警惕，多单靠止损控风险，不加仓。」（用时 6.5 秒）
- 本地小模型：「价格波动小，维持比特币多头，其他观望」（用时 466 秒）

## 假设
写在 `bills.py` 最上面，改了重跑就能看结论怎么变：
- 整机功耗 400 瓦（跑长任务时显卡实测 220–270 瓦），一次按 20 分钟算。
- 电价按每度 0.15 美元、0.55 元。
- 汇率按 1 美元 = 6.68 元。
- RTX 5070 Ti 按 1450 美元 / 11900 元。没算内存、电源和折旧，真实回本只会更慢。

## 交易实验怎么跑的
- 纯模拟：每位选手程序里起始 1 万美元，不开账户、不下真单。6 个币的永续合约，按真实行情和手续费记账。每小时整点后 20 分一轮。
- 选手：`claude` = Anthropic API `claude-opus-5-5`；`deepseek` = DeepSeek 官方 API `deepseek-v4-pro`；`qwen4b` = 一台 8G 内存的 Mac mini 上用 Ollama 跑 `qwen3:4b`。另有「一直拿 BTC」和「随机下单」两个基准，这里没放。
- 这里放的是视频引用的前 59 轮（2026-11-25 至 11-27）。实验之后还在跑。
- 这 59 轮的账户记账后来发现有错（止损写反方向时被当场按挂单价成交），所以没放权益和成交记录。决策、理由、用时、Claude 的 token 和花费都不受影响。

## 文件
- `bills.py`：复算脚本，只用 Python 标准库。
- `data/round5-cost.json`：第 1 期第 5 轮 Claude Code 三次运行的花费、用时、轮数、token，以及本地三次的用时和修对数。
- `data/trader-claude-usage.jsonl`：59 轮里 Claude 每次调用的输入/输出 token 和花费，按官方价格计。
- `data/trader-decisions.jsonl`：59 轮 × 3 位选手的决策、中文理由、用时、出错信息。

## 勘误
视频说「跑了 46 轮，总共花了 1.56 美元」。复算是前 46 轮 1.495 美元，前 48 轮才是 1.56 美元。平均每次约 3 美分、一个月约 22 美元，这两个结论不变（59 轮平均 $0.0326）。

个人实测记录，不构成任何购买或投资建议。

---

English summary: No new benchmark this time; the episode puts the bills from episodes 1–2 and an hourly "AI paper-trading" experiment side by side. `bills.py` recomputes every number in the video from `data/`. Claude Code cost $0.83–1.20 per run on the 120-file, 12-bug task (2–4 min) versus about 2 cents of electricity locally (14–24 min); a dedicated RTX 5070 Ti only pays for itself after roughly 1,400–1,500 such runs. Running Claude (claude-opus-5-5) once an hour averaged $0.033 per decision, about $22 for four weeks. Median decision time over 59 rounds: Claude 5 s, DeepSeek-V4-Pro 72 s, qwen3:4b on an 8 GB Mac mini 574 s. Correction: the video says 46 rounds cost $1.56; the first 46 rounds actually cost $1.495 ($1.56 was reached at round 48). Paper trading only; not investment or purchasing advice.
