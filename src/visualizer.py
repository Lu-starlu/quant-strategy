"""
可视化模块
生成回测结果图表，保存为图片文件，用于报告展示。

图表类型：
1. 净值曲线对比图（多策略）
2. 回撤曲线图
3. 参数寻优热力图
4. 月度盈亏柱状图
"""
import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")  # 非交互式后端，无需GUI
import matplotlib.pyplot as plt
from typing import Dict, Optional

from config.settings import CONFIG

# 设置中文字体（Mac系统）
plt.rcParams["font.sans-serif"] = ["Arial Unicode MS", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


class Visualizer:
    """回测结果可视化"""

    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = output_dir or CONFIG.output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def plot_equity_curves(self, equity_dict: Dict[str, pd.Series],
                           title: str = "策略净值曲线对比",
                           filename: str = "equity_curves.png") -> str:
        """
        绘制多策略净值曲线对比图
        :param equity_dict: {策略名: 净值Series}
        """
        fig, ax = plt.subplots(figsize=(12, 6))

        for name, equity in equity_dict.items():
            # 归一化，从1开始便于对比
            normalized = equity / equity.iloc[0]
            ax.plot(normalized.index, normalized.values, label=name, linewidth=1.5)

        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.set_xlabel("日期", fontsize=11)
        ax.set_ylabel("归一化净值", fontsize=11)
        ax.legend(loc="best", fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.axhline(y=1.0, color="gray", linestyle="--", alpha=0.5)

        plt.tight_layout()
        path = os.path.join(self.output_dir, filename)
        plt.savefig(path, dpi=150, bbox_inches="tight")
        plt.close()
        return path

    def plot_drawdown(self, equity: pd.Series, strategy_name: str,
                      filename: str = "drawdown.png") -> str:
        """绘制回撤曲线图"""
        peak = equity.cummax()
        drawdown = (equity - peak) / peak * 100

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8),
                                       gridspec_kw={"height_ratios": [3, 1]})

        # 上图：净值曲线
        ax1.plot(equity.index, equity.values, color="#2196F3", linewidth=1.5)
        ax1.set_title(f"{strategy_name} - 净值与回撤", fontsize=14, fontweight="bold")
        ax1.set_ylabel("账户净值", fontsize=11)
        ax1.grid(True, alpha=0.3)

        # 下图：回撤
        ax2.fill_between(drawdown.index, drawdown.values, 0,
                         color="#F44336", alpha=0.4)
        ax2.plot(drawdown.index, drawdown.values, color="#F44336", linewidth=1)
        ax2.set_ylabel("回撤 (%)", fontsize=11)
        ax2.set_xlabel("日期", fontsize=11)
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        path = os.path.join(self.output_dir, filename)
        plt.savefig(path, dpi=150, bbox_inches="tight")
        plt.close()
        return path

    def plot_param_heatmap(self, pivot_df: pd.DataFrame,
                           title: str = "双均线参数寻优热力图（夏普比率）",
                           filename: str = "param_heatmap.png") -> str:
        """绘制参数寻优热力图"""
        fig, ax = plt.subplots(figsize=(10, 8))

        im = ax.imshow(pivot_df.values, cmap="RdYlGn", aspect="auto",
                       vmin=np.nanmin(pivot_df.values),
                       vmax=np.nanmax(pivot_df.values))

        ax.set_xticks(range(len(pivot_df.columns)))
        ax.set_xticklabels(pivot_df.columns, fontsize=9)
        ax.set_yticks(range(len(pivot_df.index)))
        ax.set_yticklabels(pivot_df.index, fontsize=9)
        ax.set_xlabel("快线周期", fontsize=11)
        ax.set_ylabel("慢线周期", fontsize=11)
        ax.set_title(title, fontsize=14, fontweight="bold")

        # 标注数值
        for i in range(len(pivot_df.index)):
            for j in range(len(pivot_df.columns)):
                val = pivot_df.values[i, j]
                if not np.isnan(val):
                    ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                            fontsize=7, color="black")

        plt.colorbar(im, ax=ax, label="夏普比率")
        plt.tight_layout()
        path = os.path.join(self.output_dir, filename)
        plt.savefig(path, dpi=150, bbox_inches="tight")
        plt.close()
        return path

    def plot_monthly_pnl(self, trade_df: pd.DataFrame,
                         filename: str = "monthly_pnl.png") -> str:
        """绘制月度盈亏柱状图"""
        if trade_df.empty:
            return ""
        df = trade_df.copy()
        df["month"] = pd.to_datetime(df["date"]).dt.to_period("M").astype(str)
        monthly = df.groupby("month")["pnlnet"].sum()

        fig, ax = plt.subplots(figsize=(12, 5))
        colors = ["#4CAF50" if v >= 0 else "#F44336" for v in monthly.values]
        ax.bar(monthly.index, monthly.values, color=colors, alpha=0.8)
        ax.axhline(y=0, color="black", linewidth=0.8)
        ax.set_title("月度盈亏分布", fontsize=14, fontweight="bold")
        ax.set_xlabel("月份", fontsize=11)
        ax.set_ylabel("净盈亏", fontsize=11)
        ax.grid(True, alpha=0.3, axis="y")
        plt.xticks(rotation=45)
        plt.tight_layout()
        path = os.path.join(self.output_dir, filename)
        plt.savefig(path, dpi=150, bbox_inches="tight")
        plt.close()
        return path
