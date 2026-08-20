"""
单元测试 - 数据加载模块
"""
import pytest
import pandas as pd
from src.data_loader import DataLoader


class TestDataLoader:

    def test_sim_data_shape(self):
        """模拟数据应包含OHLCV五列，且行数正确"""
        loader = DataLoader()
        df = loader.load(use_sim=True)
        assert isinstance(df, pd.DataFrame)
        assert all(col in df.columns for col in ["open", "high", "low", "close", "volume"])
        assert len(df) > 0

    def test_sim_data_positive_prices(self):
        """模拟价格应为正数"""
        loader = DataLoader()
        df = loader.load(use_sim=True)
        assert (df["close"] > 0).all()
        assert (df["high"] >= df["low"]).all()
        assert (df["volume"] > 0).all()

    def test_sim_data_index_is_datetime(self):
        """索引应为datetime类型"""
        loader = DataLoader()
        df = loader.load(use_sim=True)
        assert pd.api.types.is_datetime64_any_dtype(df.index)

    def test_calculate_returns(self):
        """收益率计算应正确"""
        prices = pd.Series([100, 110, 105, 120])
        returns = DataLoader.calculate_returns(prices)
        assert len(returns) == 3
        assert abs(returns.iloc[0] - 0.1) < 0.001

    def test_calculate_log_returns(self):
        """对数收益率计算应正确"""
        prices = pd.Series([100, 110])
        log_ret = DataLoader.calculate_log_returns(prices)
        import numpy as np
        assert abs(log_ret.iloc[0] - np.log(1.1)) < 0.001

    def test_reproducible_with_seed(self):
        """相同随机种子应生成相同数据"""
        loader = DataLoader()
        df1 = loader.load(use_sim=True)
        df2 = loader.load(use_sim=True)
        pd.testing.assert_frame_equal(df1, df2)
