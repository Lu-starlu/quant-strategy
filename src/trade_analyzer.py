"""
交易归因分析模块
对策略交易日志进行多维度归因分析，回答"钱是怎么赚的、怎么亏的"。

分析维度：
1. 整体盈亏概览：总盈亏、胜率、盈亏比、期望值
2. 时间维度：按月份/季度统计盈亏，识别策略有效时段
3. 持仓周期维度：短中长线交易盈亏对比
4. 盈亏分布：单笔盈亏分布、最大盈利/亏损交易
5. 连续盈亏：最大连续盈利/亏损 streak
6. 标的维度（多标的场景）：按品种统计盈亏
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Optional


class TradeAnalyzer:
    """交易归因分析器"""

    def __init__(self, trade_log: List[Dict]):
        """
        :param trade_log: 策略输出的交易日志
        """
        self.raw_log = trade_log
        self.closed_trades = self._extract_closed_trades()
        self.df = pd.DataFrame(self.closed_trades) if self.closed_trades else pd.DataFrame()

    def _extract_closed_trades(self) -> List[Dict]:
        """从交易日志中提取平仓交易记录"""
        return [t for t in self.raw_log if t.get("action") == "CLOSE"]

    def full_report(self) -> str:
        """生成完整归因分析报告"""
        if self.df.empty:
            return "无平仓交易记录，无法进行归因分析。"

        lines = [
            "=" * 55,
            "            交易归因分析报告",
            "=" * 55,
            self._overview(),
            self._by_month(),
            self._by_holding_period(),
            self._distribution(),
            self._streak_analysis(),
            "=" * 55,
        ]
        return "\n".join(lines)

    def _overview(self) -> str:
        """整体盈亏概览"""
        df = self.df
        total_pnl = df["pnlnet"].sum()
        wins = df[df["pnlnet"] > 0]
        losses = df[df["pnlnet"] <= 0]
        win_rate = len(wins) / len(df) * 100
        avg_win = wins["pnlnet"].mean() if len(wins) > 0 else 0
        avg_loss = abs(losses["pnlnet"].mean()) if len(losses) > 0 else 0
        pl_ratio = avg_win / avg_loss if avg_loss > 0 else float("inf")
        # 单笔交易期望值 = 胜率*平均盈利 - 败率*平均亏损
        expectancy = (win_rate / 100 * avg_win) - ((100 - win_rate) / 100 * avg_loss)

        return (
            f"\n【整体盈亏概览】\n"
            f"  总交易次数:     {len(df):>8d}\n"
            f"  总净盈亏:       {total_pnl:>10.2f}\n"
            f"  盈利次数:       {len(wins):>8d}  亏损次数: {len(losses):>6d}\n"
            f"  胜率:           {win_rate:>9.2f} %\n"
            f"  平均盈利:       {avg_win:>10.2f}  平均亏损: {avg_loss:>10.2f}\n"
            f"  盈亏比:         {pl_ratio:>10.2f}\n"
            f"  单笔期望值:     {expectancy:>10.2f}  {'(正期望策略)' if expectancy > 0 else '(负期望策略)'}"
        )

    def _by_month(self) -> str:
        """按月份统计盈亏"""
        df = self.df.copy()
        df["month"] = pd.to_datetime(df["date"]).dt.to_period("M")
        monthly = df.groupby("month")["pnlnet"].agg(["sum", "count", "mean"])
        monthly.columns = ["总盈亏", "交易次数", "平均盈亏"]

        lines = ["\n【月度盈亏归因】"]
        for month, row in monthly.iterrows():
            sign = "+" if row["总盈亏"] >= 0 else ""
            lines.append(
                f"  {month}: 盈亏 {sign}{row['总盈亏']:>8.2f}  "
                f"次数 {int(row['交易次数']):>3d}  单笔均 {row['平均盈亏']:>8.2f}"
            )
        return "\n".join(lines)

    def _by_holding_period(self) -> str:
        """按持仓周期分组分析"""
        df = self.df.copy()
        # 持仓周期分箱：短线(<=5天)、中线(6-20天)、长线(>20天)
        bins = [0, 5, 20, float("inf")]
        labels = ["短线(≤5天)", "中线(6-20天)", "长线(>20天)"]
        df["holding_group"] = pd.cut(df["bars_held"], bins=bins, labels=labels, right=True)

        grouped = df.groupby("holding_group", observed=True)["pnlnet"].agg(
            ["sum", "count", "mean"]
        )
        grouped.columns = ["总盈亏", "交易次数", "平均盈亏"]

        lines = ["\n【持仓周期归因】"]
        for group, row in grouped.iterrows():
            if row["交易次数"] == 0:
                continue
            sign = "+" if row["总盈亏"] >= 0 else ""
            lines.append(
                f"  {group}: 盈亏 {sign}{row['总盈亏']:>8.2f}  "
                f"次数 {int(row['交易次数']):>3d}  单笔均 {row['平均盈亏']:>8.2f}"
            )
        return "\n".join(lines)

    def _distribution(self) -> str:
        """盈亏分布统计"""
        df = self.df
        pnl = df["pnlnet"]
        return (
            f"\n【盈亏分布】\n"
            f"  最大单笔盈利:   {pnl.max():>10.2f}\n"
            f"  最大单笔亏损:   {pnl.min():>10.2f}\n"
            f"  盈亏中位数:     {pnl.median():>10.2f}\n"
            f"  盈亏标准差:     {pnl.std():>10.2f}\n"
            f"  盈利交易占比:   {(pnl > 0).mean()*100:>9.2f} %\n"
            f"  盈亏总额比:     {pnl[pnl>0].sum() / abs(pnl[pnl<=0].sum()) if (pnl<=0).any() else float('inf'):>10.2f}"
        )

    def _streak_analysis(self) -> str:
        """连续盈亏分析"""
        pnls = self.df["pnlnet"].values
        max_win_streak = max_loss_streak = 0
        cur_win = cur_loss = 0
        for p in pnls:
            if p > 0:
                cur_win += 1
                cur_loss = 0
                max_win_streak = max(max_win_streak, cur_win)
            else:
                cur_loss += 1
                cur_win = 0
                max_loss_streak = max(max_loss_streak, cur_loss)

        return (
            f"\n【连续盈亏分析】\n"
            f"  最大连续盈利次数: {max_win_streak:>6d}\n"
            f"  最大连续亏损次数: {max_loss_streak:>6d}\n"
            f"  （连续亏损次数反映策略最大资金回撤压力）"
        )

    def to_dataframe(self) -> pd.DataFrame:
        """导出交易明细DataFrame"""
        return self.df.copy()
