import backtrader as bt
import pandas as pd
import numpy as np

# 生成模拟ETF行情数据
def generate_sim_data(days=500):
    np.random.seed(666)
    price = 1.0
    data_list = []
    for i in range(days):
        ret = np.random.normal(0.0005, 0.018)
        price *= (1 + ret)
        date = pd.Timestamp("2024-01-01") + pd.Timedelta(i, unit="D")
        data_list.append({
            "datetime": date,
            "open": price*0.998,
            "high": price*1.005,
            "low": price*0.995,
            "close": price,
            "volume": 1000000
        })
    df = pd.DataFrame(data_list)
    df.set_index("datetime", inplace=True)
    return df


# 双均线策略
class DualMA(bt.Strategy):
    params = (
        ("fast_period", 10),
        ("slow_period", 30),
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

# 分析器：回测指标
if __name__ == "__main__":
    cerebro = bt.Cerebro()
    cerebro.addstrategy(DualMA)

    df_sim = generate_sim_data(500)
    data = bt.feeds.PandasData(dataname=df_sim)
    cerebro.adddata(data)

    cerebro.broker.setcash(100000.0)
    cerebro.broker.setcommission(0.0003)

    # 关键量化指标分析器
    cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe", riskfreerate=0.02)

    print("初始资金：%.2f" % cerebro.broker.getvalue())
    result = cerebro.run()
    strat = result[0]
    print("期末资金：%.2f" % cerebro.broker.getvalue())

    ret_ana = strat.analyzers.returns.get_analysis()
    dd_ana = strat.analyzers.drawdown.get_analysis()
    sharpe_ana = strat.analyzers.sharpe.get_analysis()

    print("\n==========回测核心指标==========")
    print(f"总收益率：{ret_ana['rnorm100']:.2f} %")
    print(f"年化收益率：{ret_ana['rnorm100']/2:.2f} %")
    print(f"最大回撤：{dd_ana['max']['drawdown']:.2f} %")
    print(f"夏普比率：{sharpe_ana['sharperatio']:.3f}")
