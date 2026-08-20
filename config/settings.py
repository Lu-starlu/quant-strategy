"""
全局配置文件
集中管理回测参数、标的信息、交易成本等，避免硬编码散落在各模块中
"""
from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class BacktestConfig:
    """回测核心配置"""
    initial_cash: float = 1_000_000.0          # 初始资金 100万
    commission_rate: float = 0.0003            # 佣金费率 万三
    slippage: float = 0.001                    # 滑点 千一
    stamp_duty: float = 0.001                  # 印花税（卖出时收取）
    risk_free_rate: float = 0.025              # 无风险利率（年化），用于夏普比率
    trading_days_per_year: int = 252           # 年化交易日数


@dataclass
class DataConfig:
    """数据配置"""
    # 默认回测标的：沪深300ETF
    default_symbol: str = "510300.SS"
    start_date: str = "2022-01-01"
    end_date: str = "2026-08-01"
    # 模拟数据参数
    sim_days: int = 1000
    sim_initial_price: float = 3.0
    sim_daily_return_mean: float = 0.0003
    sim_daily_return_std: float = 0.015
    sim_random_seed: int = 42


@dataclass
class StrategyConfig:
    """策略参数配置（默认双均线）"""
    fast_period: int = 5
    slow_period: int = 20
    # 参数寻优范围
    fast_range: Tuple[int, int] = (3, 20)
    slow_range: Tuple[int, int] = (20, 60)


@dataclass
class ProjectConfig:
    """项目总配置"""
    backtest: BacktestConfig = field(default_factory=BacktestConfig)
    data: DataConfig = field(default_factory=DataConfig)
    strategy: StrategyConfig = field(default_factory=StrategyConfig)
    output_dir: str = "output"
    # 支持的策略列表
    supported_strategies: List[str] = field(
        default_factory=lambda: ["DualMA", "MACDStrategy", "BollingerStrategy"]
    )


# 全局单例
CONFIG = ProjectConfig()
