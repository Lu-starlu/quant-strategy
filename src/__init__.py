"""src包初始化
采用延迟导入，backtrader相关模块在实际使用时才导入，
避免未安装backtrader时核心模块（数据/指标/归因）无法使用。
"""
from src.data_loader import DataLoader
from src.metrics import PerformanceMetrics
from src.trade_analyzer import TradeAnalyzer

__all__ = [
    "DataLoader",
    "PerformanceMetrics",
    "TradeAnalyzer",
]


def __getattr__(name):
    """延迟导入backtrader相关模块"""
    if name in ("STRATEGY_REGISTRY", "DualMA", "MACDStrategy", "BollingerStrategy"):
        from src.strategies import (
            STRATEGY_REGISTRY, DualMA, MACDStrategy, BollingerStrategy
        )
        return locals().get(name) or eval(name)
    if name == "BacktestEngine":
        from src.backtest_engine import BacktestEngine
        return BacktestEngine
    if name == "ParameterOptimizer":
        from src.optimizer import ParameterOptimizer
        return ParameterOptimizer
    if name == "Visualizer":
        from src.visualizer import Visualizer
        return Visualizer
    raise AttributeError(f"module 'src' has no attribute {name!r}")
