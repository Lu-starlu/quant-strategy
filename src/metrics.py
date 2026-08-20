"""
绩效指标计算模块
独立于backtrader内置分析器，手动实现全套量化绩效评价指标，
便于理解底层逻辑，也支持对任意净值序列进行评估。

指标清单：
- 绝对收益：总收益率、年化收益率
- 风险指标：最大回撤、年化波动率、下行波动率
- 风险调整收益：夏普比率、索提诺比率、卡玛比率
- 交易统计：胜率、盈亏比、平均持仓周期、最大连续亏损
"""
import numpy as np
import pandas as pd
from typing import Dict, Optional


class PerformanceMetrics:
    """绩效指标计算器"""

    def __init__(self, risk_free_rate: float = 0.025, trading_days: int = 252):
        self.rf = risk_free_rate
        self.trading_days = trading_days

    def calculate_all(self, equity_curve: pd.Series,
                      trade_log: Optional[list] = None) -> Dict:
        """
        计算全部绩效指标
        :param equity_curve: 净值曲线（账户总值时间序列）
        :param trade_log: 交易日志列表，用于交易统计
        :return: 指标字典
        """
        returns = equity_curve.pct_change().dropna()

        metrics = {
            # 收益指标
            "total_return": self.total_return(equity_curve),
            "annual_return": self.annual_return(equity_curve),
            # 风险指标
            "max_drawdown": self.max_drawdown(equity_curve),
            "annual_volatility": self.annual_volatility(returns),
            "downside_volatility": self.downside_volatility(returns),
            # 风险调整收益
            "sharpe_ratio": self.sharpe_ratio(returns),
            "sortino_ratio": self.sortino_ratio(returns),
            "calmar_ratio": self.calmar_ratio(equity_curve),
            # 基础信息
            "final_equity": float(equity_curve.iloc[-1]),
            "trading_days": len(equity_curve),
        }

        # 交易统计（如果有交易日志）
        if trade_log is not None:
            trade_stats = self._calculate_trade_stats(trade_log)
            metrics.update(trade_stats)

        return metrics

    # ---------- 收益指标 ----------

    @staticmethod
    def total_return(equity: pd.Series) -> float:
        """总收益率"""
        return (equity.iloc[-1] / equity.iloc[0] - 1) * 100

    def annual_return(self, equity: pd.Series) -> float:
        """年化收益率（复利）"""
        total_days = len(equity)
        total_ret = equity.iloc[-1] / equity.iloc[0]
        if total_ret <= 0:
            return -100.0
        years = total_days / self.trading_days
        return (total_ret ** (1 / years) - 1) * 100

    # ---------- 风险指标 ----------

    @staticmethod
    def max_drawdown(equity: pd.Series) -> float:
        """最大回撤（百分比）"""
        peak = equity.cummax()
        drawdown = (equity - peak) / peak
        return drawdown.min() * 100

    def annual_volatility(self, returns: pd.Series) -> float:
        """年化波动率"""
        return returns.std() * np.sqrt(self.trading_days) * 100

    def downside_volatility(self, returns: pd.Series) -> float:
        """下行波动率（只统计负收益）"""
        downside = returns[returns < 0]
        if len(downside) == 0:
            return 0.0
        return downside.std() * np.sqrt(self.trading_days) * 100

    # ---------- 风险调整收益 ----------

    def sharpe_ratio(self, returns: pd.Series) -> float:
        """夏普比率 = (年化收益 - 无风险利率) / 年化波动率"""
        excess_return = returns.mean() * self.trading_days - self.rf
        vol = returns.std() * np.sqrt(self.trading_days)
        if vol == 0:
            return 0.0
        return excess_return / vol

    def sortino_ratio(self, returns: pd.Series) -> float:
        """索提诺比率 = 超额收益 / 下行波动率"""
        excess_return = returns.mean() * self.trading_days - self.rf
        downside_vol = self.downside_volatility(returns) / 100
        if downside_vol == 0:
            return 0.0
        return excess_return / downside_vol

    def calmar_ratio(self, equity: pd.Series) -> float:
        """卡玛比率 = 年化收益 / 最大回撤"""
        ann_ret = self.annual_return(equity) / 100
        mdd = abs(self.max_drawdown(equity)) / 100
        if mdd == 0:
            return 0.0
        return ann_ret / mdd

    # ---------- 交易统计 ----------

    @staticmethod
    def _calculate_trade_stats(trade_log: list) -> Dict:
        """从交易日志中提取平仓交易，计算胜率、盈亏比等"""
        closed_trades = [t for t in trade_log if t.get("action") == "CLOSE"]
        if not closed_trades:
            return {
                "total_trades": 0,
                "win_rate": 0.0,
                "profit_loss_ratio": 0.0,
                "avg_holding_bars": 0,
                "max_consecutive_losses": 0,
            }

        pnls = [t["pnlnet"] for t in closed_trades]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p <= 0]

        # 最大连续亏损
        max_consec_loss = 0
        current_loss = 0
        for p in pnls:
            if p <= 0:
                current_loss += 1
                max_consec_loss = max(max_consec_loss, current_loss)
            else:
                current_loss = 0

        avg_win = np.mean(wins) if wins else 0
        avg_loss = abs(np.mean(losses)) if losses else 0

        return {
            "total_trades": len(closed_trades),
            "win_rate": (len(wins) / len(closed_trades)) * 100,
            "profit_loss_ratio": avg_win / avg_loss if avg_loss > 0 else float("inf"),
            "avg_holding_bars": int(np.mean([t["bars_held"] for t in closed_trades])),
            "max_consecutive_losses": max_consec_loss,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
        }

    @staticmethod
    def format_metrics(metrics: Dict) -> str:
        """格式化输出指标报告"""
        lines = [
            "=" * 50,
            "           量化策略绩效评估报告",
            "=" * 50,
            f"  期末净值:       {metrics['final_equity']:>12,.2f}",
            f"  交易天数:       {metrics['trading_days']:>12d}",
            "-" * 50,
            "  【收益指标】",
            f"  总收益率:       {metrics['total_return']:>11.2f} %",
            f"  年化收益率:     {metrics['annual_return']:>11.2f} %",
            "-" * 50,
            "  【风险指标】",
            f"  最大回撤:       {metrics['max_drawdown']:>11.2f} %",
            f"  年化波动率:     {metrics['annual_volatility']:>11.2f} %",
            f"  下行波动率:     {metrics['downside_volatility']:>11.2f} %",
            "-" * 50,
            "  【风险调整收益】",
            f"  夏普比率:       {metrics['sharpe_ratio']:>12.3f}",
            f"  索提诺比率:     {metrics['sortino_ratio']:>12.3f}",
            f"  卡玛比率:       {metrics['calmar_ratio']:>12.3f}",
        ]
        if metrics.get("total_trades", 0) > 0:
            lines += [
                "-" * 50,
                "  【交易统计】",
                f"  总交易次数:     {metrics['total_trades']:>12d}",
                f"  胜率:           {metrics['win_rate']:>11.2f} %",
                f"  盈亏比:         {metrics['profit_loss_ratio']:>12.2f}",
                f"  平均持仓天数:   {metrics['avg_holding_bars']:>12d}",
                f"  最大连续亏损:   {metrics['max_consecutive_losses']:>12d}",
            ]
        lines.append("=" * 50)
        return "\n".join(lines)
