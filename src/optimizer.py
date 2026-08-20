"""
参数寻优模块
使用网格搜索(Grid Search)对策略参数进行遍历寻优，
评估不同参数组合下的绩效表现，输出参数热力图数据。

支持寻优目标：夏普比率、年化收益率、卡玛比率
"""
import itertools
import pandas as pd
from typing import Dict, List, Tuple, Callable, Optional

from config.settings import CONFIG
from src.backtest_engine import BacktestEngine


class ParameterOptimizer:
    """策略参数网格寻优"""

    def __init__(self, engine: BacktestEngine):
        self.engine = engine
        self.cfg = CONFIG.strategy

    def grid_search_dual_ma(self, data: pd.DataFrame,
                            objective: str = "sharpe_ratio") -> pd.DataFrame:
        """
        双均线策略参数网格搜索
        :param data: 行情数据
        :param objective: 优化目标，可选 sharpe_ratio / annual_return / calmar_ratio
        :return: 参数组合绩效DataFrame
        """
        fast_values = list(range(self.cfg.fast_range[0], self.cfg.fast_range[1] + 1))
        slow_values = list(range(self.cfg.slow_range[0], self.cfg.slow_range[1] + 1))

        results = []
        total = len(fast_values) * len(slow_values)
        count = 0

        for fast, slow in itertools.product(fast_values, slow_values):
            if fast >= slow:
                continue  # 快线必须慢于慢线，跳过无效组合
            count += 1
            if count % 20 == 0:
                print(f"[寻优进度] {count}/{total - len(fast_values)} 组合已测试")

            try:
                result = self.engine.run_single(
                    data, "DualMA",
                    strategy_params={"fast_period": fast, "slow_period": slow}
                )
                metrics = result["metrics"]
                results.append({
                    "fast_period": fast,
                    "slow_period": slow,
                    "sharpe_ratio": metrics.get("sharpe_ratio", 0),
                    "annual_return": metrics.get("annual_return", 0),
                    "max_drawdown": metrics.get("max_drawdown", 0),
                    "calmar_ratio": metrics.get("calmar_ratio", 0),
                    "total_trades": metrics.get("total_trades", 0),
                })
            except Exception as e:
                print(f"[跳过] fast={fast}, slow={slow} 报错: {e}")

        df = pd.DataFrame(results)
        if df.empty:
            return df

        # 按优化目标排序
        df = df.sort_values(by=objective, ascending=False).reset_index(drop=True)
        return df

    @staticmethod
    def get_best_params(search_df: pd.DataFrame,
                        objective: str = "sharpe_ratio") -> Dict:
        """获取最优参数组合"""
        if search_df.empty:
            return {}
        best = search_df.iloc[0]
        return {
            "fast_period": int(best["fast_period"]),
            "slow_period": int(best["slow_period"]),
            objective: float(best[objective]),
            "annual_return": float(best["annual_return"]),
            "max_drawdown": float(best["max_drawdown"]),
        }

    @staticmethod
    def pivot_heatmap_data(search_df: pd.DataFrame,
                           value_col: str = "sharpe_ratio") -> pd.DataFrame:
        """生成热力图数据（透视表），行=慢线，列=快线"""
        return search_df.pivot(
            index="slow_period",
            columns="fast_period",
            values=value_col
        )

    @staticmethod
    def print_top_n(search_df: pd.DataFrame, n: int = 10,
                    objective: str = "sharpe_ratio"):
        """打印Top N参数组合"""
        print(f"\n{'='*60}")
        print(f"  参数寻优结果 Top {n}（按 {objective} 排序）")
        print(f"{'='*60}")
        cols = ["fast_period", "slow_period", objective,
                "annual_return", "max_drawdown", "total_trades"]
        print(search_df[cols].head(n).to_string(index=False, float_format="%.4f"))
        print(f"{'='*60}")
