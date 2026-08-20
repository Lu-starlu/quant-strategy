import backtrader as bt
import pandas as pd
import numpy as np
from datetime import datetime,timedelta

# 双均线策略
class DualMA(bt.Strategy):
    params = (
        ("fast_period",5),
        ("slow_period",20),
    )

    def __init__(self):
        self.ma_fast = bt.ind.SMA(period=self.p.fast_period)
        self.ma_slow = bt.ind.SMA(period=self.p.slow_period)
        self.crossover = bt.ind.CrossOver(self.ma_fast, self.ma_slow)

    def next(self):
        if not self.position:
            if self.crossover > 0:
                self.buy(size=100)
        else:
            if self.crossover < 0:
                self.close()


# 生成模拟ETF行情，不需要网络
def make_sim_data(start_date="2022-01-01", end_date="2026-08-01"):
    start = datetime.strptime(start_date,"%Y-%m-%d")
    end = datetime.strptime(end_date,"%Y-%m-%d")
    dates = []
    current = start
    np.random.seed(42)
    price = 3.0
    o,h,l,c,vol = [],[],[],[],[]
    while current <= end:
        # 简单模拟交易日，跳过周末
        if current.weekday() <5:
            dates.append(current)
            ret = np.random.normal(0,0.012)
            price *= (1+ret)
            openp = price * (1+np.random.normal(0,0.003))
            highp = max(openp,price)*(1+abs(np.random.normal(0,0.005)))
            lowp = min(openp,price)*(1-abs(np.random.normal(0,0.005)))
            o.append(openp)
            h.append(highp)
            l.append(lowp)
            c.append(price)
            vol.append(np.random.randint(500000,3000000))
        current += timedelta(days=1)
    df = pd.DataFrame({
        "open":o,"high":h,"low":l,"close":c,"volume":vol
    },index=dates)
    return df


if __name__ == "__main__":
    cerebro = bt.Cerebro()
    cerebro.addstrategy(DualMA)

    df_sim = make_sim_data()
    data = bt.feeds.PandasData(dataname=df_sim)
    cerebro.adddata(data)

    cerebro.broker.setcash(100000)
    cerebro.broker.setcommission(0.0003)

    print(f"初始资金：{cerebro.broker.getvalue():.2f}")
    result = cerebro.run()
    final_val = cerebro.broker.getvalue()
    print(f"回测结束资产：{final_val:.2f}")
    print(f"策略总收益率：{(final_val/100000 -1)*100:.2f} %")
