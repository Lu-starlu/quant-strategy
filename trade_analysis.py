import pandas as pd
import numpy as np

# 模拟交易日志，后续替换成自己实习的真实交易数据
trade_data = [
    {"date":"2024-02-01","code":"510300","direction":"buy","pnl":120,"period":"morning"},
    {"date":"2024-02-05","code":"510300","direction":"sell","pnl":-85,"period":"afternoon"},
    {"date":"2024-02-10","code":"159915","direction":"buy","pnl":210,"period":"morning"},
    {"date":"2024-02-12","code":"159915","direction":"sell","pnl":-30,"period":"afternoon"},
]

df = pd.DataFrame(trade_data)

print("====整体盈亏汇总====")
print(f"总盈亏：{df['pnl'].sum()}")
print(f"盈利交易次数：{len(df[df['pnl']>0])}")
print(f"亏损交易次数：{len(df[df['pnl']<0])}")

print("\n====按标的盈亏归因====")
print(df.groupby("code")["pnl"].agg(["sum","count"]))

print("\n====按交易时段盈亏归因====")
print(df.groupby("period")["pnl"].agg(["sum","count"]))
