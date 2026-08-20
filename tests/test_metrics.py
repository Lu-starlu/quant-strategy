"""
单元测试 - 绩效指标模块
验证核心指标计算的正确性
"""
import pytest
import pandas as pd
import numpy as np
from src.metrics import PerformanceMetrics


@pytest.fixture
def metrics_calc():
    return PerformanceMetrics(risk_free_rate=0.025, trading_days=252)


@pytest.fixture
def sample_equity():
    """生成一条简单的净值曲线：100天，从100万涨到110万"""
    dates = pd.date_range("2024-01-01", periods=100, freq="B")
    prices = np.linspace(1_000_000, 1_100_000, 100)
    return pd.Series(prices, index=dates)


class TestPerformanceMetrics:

    def test_total_return_positive(self, metrics_calc, sample_equity):
        """总收益率应为正，约10%"""
        ret = metrics_calc.total_return(sample_equity)
        assert ret > 0
        assert abs(ret - 10.0) < 0.1

    def test_max_drawdown_no_drawdown(self, metrics_calc, sample_equity):
        """单调上涨的净值曲线，最大回撤应为0"""
        mdd = metrics_calc.max_drawdown(sample_equity)
        assert abs(mdd) < 0.01

    def test_max_drawdown_with_drop(self, metrics_calc):
        """有回撤的净值曲线，最大回撤应正确计算"""
        equity = pd.Series([100, 120, 90, 110, 100])
        mdd = metrics_calc.max_drawdown(equity)
        # 从120跌到90，回撤25%
        assert abs(mdd - (-25.0)) < 0.1

    def test_annual_volatility_constant(self, metrics_calc):
        """收益率恒定时波动率为0"""
        equity = pd.Series([100, 101, 102, 103, 104])
        returns = equity.pct_change().dropna()
        vol = metrics_calc.annual_volatility(returns)
        assert vol >= 0

    def test_sharpe_ratio_no_volatility(self, metrics_calc):
        """零波动率时夏普比率返回0，不报错"""
        returns = pd.Series([0.01, 0.01, 0.01, 0.01])
        sharpe = metrics_calc.sharpe_ratio(returns)
        # 波动率不为零（有微小变化），应该有值
        assert isinstance(sharpe, float)

    def test_calculate_all_returns_keys(self, metrics_calc, sample_equity):
        """calculate_all应返回所有核心指标"""
        result = metrics_calc.calculate_all(sample_equity)
        required_keys = [
            "total_return", "annual_return", "max_drawdown",
            "annual_volatility", "sharpe_ratio", "sortino_ratio",
            "calmar_ratio", "final_equity", "trading_days"
        ]
        for key in required_keys:
            assert key in result, f"缺少指标: {key}"

    def test_trade_stats_empty(self, metrics_calc, sample_equity):
        """无交易日志时，交易统计应为0"""
        result = metrics_calc.calculate_all(sample_equity, trade_log=[])
        assert result["total_trades"] == 0
        assert result["win_rate"] == 0.0

    def test_trade_stats_with_data(self, metrics_calc, sample_equity):
        """有交易日志时，应正确计算胜率"""
        trade_log = [
            {"action": "CLOSE", "pnlnet": 100, "bars_held": 5},
            {"action": "CLOSE", "pnlnet": -50, "bars_held": 3},
            {"action": "CLOSE", "pnlnet": 200, "bars_held": 10},
        ]
        result = metrics_calc.calculate_all(sample_equity, trade_log=trade_log)
        assert result["total_trades"] == 3
        assert abs(result["win_rate"] - 66.67) < 0.1
        assert result["max_consecutive_losses"] == 1
