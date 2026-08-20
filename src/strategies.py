"""
策略模块
实现三种经典量化交易策略，统一继承自backtrader.Strategy
1. DualMA       - 双均线交叉策略（趋势跟踪）
2. MACDStrategy - MACD金叉死叉策略（动量指标）
3. BollingerStrategy - 布林带均值回归策略（震荡指标）
每个策略都记录交易日志，供后续归因分析使用
"""
import backtrader as bt
from typing import List, Dict


class BaseStrategy(bt.Strategy):
    """策略基类，统一交易日志记录"""

    def __init__(self):
        self.trade_log: List[Dict] = []
        self.order = None

    def notify_order(self, order):
        """订单状态回调"""
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status in [order.Completed]:
            if order.isbuy():
                self.trade_log.append({
                    "date": self.datas[0].datetime.date(0).isoformat(),
                    "action": "BUY",
                    "price": order.executed.price,
                    "size": order.executed.size,
                    "cost": order.executed.value,
                    "commission": order.executed.comm
                })
            else:
                self.trade_log.append({
                    "date": self.datas[0].datetime.date(0).isoformat(),
                    "action": "SELL",
                    "price": order.executed.price,
                    "size": order.executed.size,
                    "cost": order.executed.value,
                    "commission": order.executed.comm
                })
        self.order = None

    def notify_trade(self, trade):
        """交易平仓回调，记录每笔完整交易盈亏"""
        if trade.isclosed:
            self.trade_log.append({
                "date": self.datas[0].datetime.date(0).isoformat(),
                "action": "CLOSE",
                "pnl": trade.pnl,
                "pnlnet": trade.pnlcomm,
                "bars_held": trade.barlen
            })


class DualMA(BaseStrategy):
    """
    双均线交叉策略
    逻辑：短期均线上穿长期均线（金叉）买入，下穿（死叉）卖出
    适用：趋势行情
    """
    params = (
        ("fast_period", 5),
        ("slow_period", 20),
    )

    def __init__(self):
        super().__init__()
        self.ma_fast = bt.ind.SMA(period=self.p.fast_period)
        self.ma_slow = bt.ind.SMA(period=self.p.slow_period)
        self.crossover = bt.ind.CrossOver(self.ma_fast, self.ma_slow)

    def next(self):
        if self.order:
            return
        if not self.position:
            if self.crossover > 0:  # 金叉
                self.order = self.buy(size=1000)
        else:
            if self.crossover < 0:  # 死叉
                self.order = self.close()


class MACDStrategy(BaseStrategy):
    """
    MACD策略
    逻辑：MACD线上穿信号线（金叉）买入，下穿（死叉）卖出
    适用：动量趋势确认
    """
    params = (
        ("fast_period", 12),
        ("slow_period", 26),
        ("signal_period", 9),
    )

    def __init__(self):
        super().__init__()
        self.macd = bt.ind.MACD(
            period_me1=self.p.fast_period,
            period_me2=self.p.slow_period,
            period_signal=self.p.signal_period
        )
        self.crossover = bt.ind.CrossOver(self.macd.macd, self.macd.signal)

    def next(self):
        if self.order:
            return
        if not self.position:
            if self.crossover > 0:
                self.order = self.buy(size=1000)
        else:
            if self.crossover < 0:
                self.order = self.close()


class BollingerStrategy(BaseStrategy):
    """
    布林带均值回归策略
    逻辑：价格触及下轨买入，触及上轨卖出
    适用：震荡行情
    """
    params = (
        ("period", 20),
        ("devfactor", 2.0),
    )

    def __init__(self):
        super().__init__()
        self.boll = bt.ind.BollingerBands(
            period=self.p.period,
            devfactor=self.p.devfactor
        )

    def next(self):
        if self.order:
            return
        if not self.position:
            if self.data.close < self.boll.lines.bot:  # 触及下轨
                self.order = self.buy(size=1000)
        else:
            if self.data.close > self.boll.lines.top:  # 触及上轨
                self.order = self.close()


# 策略注册表，供引擎按名称调用
STRATEGY_REGISTRY = {
    "DualMA": DualMA,
    "MACDStrategy": MACDStrategy,
    "BollingerStrategy": BollingerStrategy,
}
