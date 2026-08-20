"""
回测引擎模块
封装backtrader，提供统一的回测接口：
- 单策略回测
- 多策略对比回测
- 返回净值曲线、交易日志、绩效指标
将底层框架细节与业务逻辑解耦，便于扩展和维护
"""
import backtrader as bt
import pandas as pd
from typing import Dict, List, Optional, Tuple

from config.settings import CONFIG
from src.strategies import STRATEGY_REGISTRY, BaseStrategy
from src.metrics import PerformanceMetrics


class BacktestEngine:
    """回测引擎封装"""

    def __init__(self, config=None):
        self.cfg = config or CONFIG
        self.metrics_calculator = PerformanceMetrics(
            risk_free_rate=self.cfg.backtest.risk_free_rate,
            trading_days=self.cfg.backtest.trading_days_per_year
        )

    def run_single(self, data: pd.DataFrame, strategy_name: str,
                   strategy_params: Optional[Dict] = None) -> Dict:
        """
        运行单策略回测
        :param data: OHLCV行情数据
        :param strategy_name: 策略名称（需在STRATEGY_REGISTRY中注册）
        :param strategy_params: 策略参数字典
        :return: 回测结果字典，含净值曲线、交易日志、绩效指标
        """
        cerebro = self._build_cerebro(strategy_name, strategy_params)
        bt_data = bt.feeds.PandasData(dataname=data)
        cerebro.adddata(bt_data)

        # 记录每日净值
        equity_curve = []
        cerebro.addanalyzer(bt.analyzers.TimeReturn, _name="timereturn")

        results = cerebro.run()
        strat = results[0]

        # 提取净值曲线
        timereturn = strat.analyzers.timereturn.get_analysis()
        if timereturn:
            equity_series = pd.Series(timereturn)
            equity_curve = (1 + equity_series).cumprod() * self.cfg.backtest.initial_cash
        else:
            equity_curve = pd.Series([self.cfg.backtest.initial_cash])

        # 计算绩效指标
        metrics = self.metrics_calculator.calculate_all(
            equity_curve,
            trade_log=getattr(strat, "trade_log", [])
        )

        return {
            "strategy_name": strategy_name,
            "strategy_params": strategy_params or {},
            "equity_curve": equity_curve,
            "trade_log": getattr(strat, "trade_log", []),
            "metrics": metrics,
            "final_value": cerebro.broker.getvalue(),
        }

    def run_comparison(self, data: pd.DataFrame,
                       strategy_list: List[Tuple[str, Optional[Dict]]]) -> pd.DataFrame:
        """
        多策略对比回测
        :param data: 行情数据
        :param strategy_list: [(策略名, 参数字典), ...]
        :return: 各策略绩效指标对比DataFrame
        """
        all_results = []
        equity_dict = {}

        for name, params in strategy_list:
            print(f"[回测中] 策略: {name} 参数: {params or '默认'}")
            result = self.run_single(data, name, params)
            metrics_row = {"strategy": name, **result["metrics"]}
            all_results.append(metrics_row)
            equity_dict[name] = result["equity_curve"]

        comparison_df = pd.DataFrame(all_results).set_index("strategy")
        return comparison_df, equity_dict

    def _build_cerebro(self, strategy_name: str,
                       strategy_params: Optional[Dict] = None) -> bt.Cerebro:
        """构建cerebro实例，统一配置资金、手续费、滑点"""
        cerebro = bt.Cerebro()

        strategy_cls = STRATEGY_REGISTRY.get(strategy_name)
        if strategy_cls is None:
            raise ValueError(f"未知策略: {strategy_name}，支持: {list(STRATEGY_REGISTRY.keys())}")

        if strategy_params:
            cerebro.addstrategy(strategy_cls, **strategy_params)
        else:
            cerebro.addstrategy(strategy_cls)

        bt_cfg = self.cfg.backtest
        cerebro.broker.setcash(bt_cfg.initial_cash)
        cerebro.broker.setcommission(commission=bt_cfg.commission_rate)
        cerebro.broker.set_slippage_perc(perc=bt_cfg.slippage)

        return cerebro

    @staticmethod
    def print_result(result: Dict):
        """打印单策略回测结果"""
        print(f"\n策略: {result['strategy_name']}")
        print(f"参数: {result['strategy_params']}")
        print(PerformanceMetrics.format_metrics(result["metrics"]))

    @staticmethod
    def print_comparison(comparison_df: pd.DataFrame):
        """打印多策略对比结果"""
        print("\n" + "=" * 70)
        print("                    多策略绩效对比")
        print("=" * 70)
        display_cols = [
            "total_return", "annual_return", "max_drawdown",
            "sharpe_ratio", "sortino_ratio", "total_trades", "win_rate"
        ]
        available = [c for c in display_cols if c in comparison_df.columns]
        print(comparison_df[available].to_string(float_format="%.3f"))
        print("=" * 70)
