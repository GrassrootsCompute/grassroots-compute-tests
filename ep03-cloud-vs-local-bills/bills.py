"""第 3 期账单复算：python3 bills.py

只用本目录 data/ 下的数据，加上下面写明的假设，算出视频里的每个数字。
假设都放在最上面，改一个数就能看结论怎么变。
"""
import json
import statistics
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent / "data"

# ---- 假设（视频用的值）----
PC_WATTS = 400            # 整机功耗按 400 瓦估（显卡实测 220–270 瓦）
LOCAL_MINUTES = 20        # 本地跑一次长任务按 20 分钟算（实测 14–24 分钟）
POWER_USD_PER_KWH = 0.15  # 电价（美元版）
POWER_CNY_PER_KWH = 0.55  # 电价（人民币版）
USD_TO_CNY = 6.68         # 汇率
GPU_USD = 1450            # RTX 5070 Ti 当时价格，「1400 多美元」
GPU_CNY = 11900           # 人民币版，「一万一千九百多」
ROUNDS_PER_DAY = 24       # 交易实验每小时一轮
DAYS = 28                 # 4 周


def main():
    r5 = json.loads((HERE / "round5-cost.json").read_text())
    cost = [x["total_cost_usd"] for x in r5["claude_code"]]
    secs = [x["duration_s"] for x in r5["claude_code"]]
    local_secs = [x["seconds"] for x in r5["local"]]
    kwh = PC_WATTS * LOCAL_MINUTES / 60 / 1000
    usd_local = kwh * POWER_USD_PER_KWH
    cny_local = kwh * POWER_CNY_PER_KWH
    mean_cost = statistics.mean(cost)

    print("== 长任务（第 1 期第 5 轮，120 个文件 12 个 bug）==")
    print(f"Claude Code 每次：{', '.join(f'${c:.2f}' for c in cost)} → 0.8–1.2 美元；"
          f"人民币 {min(cost) * USD_TO_CNY:.1f}–{max(cost) * USD_TO_CNY:.1f} 元")
    print(f"Claude 用时：{', '.join(f'{s / 60:.1f}' for s in secs)} 分钟；"
          f"本地用时：{', '.join(f'{s / 60:.1f}' for s in local_secs)} 分钟")
    print(f"本地电费：{PC_WATTS} 瓦 × {LOCAL_MINUTES} 分钟 = {kwh:.3f} 度 → "
          f"${usd_local:.3f}（约 2 美分），¥{cny_local:.3f}（约 7 分钱）")
    save_usd = mean_cost - usd_local
    save_cny = mean_cost * USD_TO_CNY - cny_local
    print(f"买 5070 Ti 回本：${GPU_USD} ÷ 每次省 ${save_usd:.2f} = {GPU_USD / save_usd:.0f} 次（视频说约 1500 次）；"
          f"¥{GPU_CNY} ÷ 每次省 ¥{save_cny:.2f} = {GPU_CNY / save_cny:.0f} 次（约 1800 次）")

    print("\n== 交易实验：Claude 每小时一次 ==")
    usage = [json.loads(l) for l in (HERE / "trader-claude-usage.jsonl").open()]
    running = 0.0
    for i, u in enumerate(usage, 1):
        running += u["usd"]
        if i in (46, 48, len(usage)):
            print(f"前 {i} 轮累计 ${running:.3f}")
    avg = running / len(usage)
    print(f"平均每轮 ${avg:.4f}（约 3 美分）；输入约 {statistics.mean(u['input_tokens'] for u in usage):.0f} token，"
          f"输出约 {statistics.mean(u['output_tokens'] for u in usage):.0f} token")
    month = avg * ROUNDS_PER_DAY * DAYS
    print(f"4 周外推：${avg:.4f} × {ROUNDS_PER_DAY} × {DAYS} = ${month:.1f}（约 22 美元），≈ ¥{month * USD_TO_CNY:.0f}（约 150 元）")

    print("\n== 交易实验：每次决策用时（中位数）==")
    lat = defaultdict(list)
    for l in (HERE / "trader-decisions.jsonl").open():
        d = json.loads(l)
        if d["latency_s"] is not None:
            lat[d["who"]].append(d["latency_s"])
    for who, xs in lat.items():
        print(f"{who:9s} {len(xs)} 轮，中位数 {statistics.median(xs):.1f} 秒")


if __name__ == "__main__":
    main()
