"""
数据加载模块
支持两种数据源：
1. 模拟行情数据（默认，无需网络，用于策略逻辑验证）
2. 真实行情数据（通过yfinance获取，需网络，可选）
统一输出标准OHLCV格式的DataFrame，供回测引擎使用
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional

from config.settings import CONFIG


class DataLoader:
    """数据加载器，统一数据接口"""

    def __init__(self, config=None):
        self.cfg = config or CONFIG.data

    def load(self, use_sim: bool = True, symbol: Optional[str] = None) -> pd.DataFrame:
        """
        加载行情数据
        :param use_sim: 是否使用模拟数据，默认True
        :param symbol: 标的代码，use_sim=False时生效
        :return: 标准OHLCV DataFrame，index为datetime
        """
        if use_sim:
            return self._generate_simulated_data()
        else:
            return self._download_real_data(symbol or self.cfg.default_symbol)

    def _generate_simulated_data(self) -> pd.DataFrame:
        """
        生成带趋势+波动的模拟ETF行情数据
        使用几何布朗运动(GBM)模型，比纯随机更贴近真实金融时间序列特征
        """
        cfg = self.cfg
        np.random.seed(cfg.sim_random_seed)

        dates = self._generate_trading_dates(cfg.sim_days)
        n = len(dates)

        # 几何布朗运动模拟价格路径
        daily_returns = np.random.normal(
            cfg.sim_daily_return_mean,
            cfg.sim_daily_return_std,
            n
        )
        # 加入轻微均值回归，避免单边趋势过强
        price = cfg.sim_initial_price
        prices = []
        for ret in daily_returns:
            price *= (1 + ret)
            prices.append(price)
        prices = np.array(prices)

        # 基于收盘价生成OHLC
        open_prices = prices * (1 + np.random.normal(0, 0.002, n))
        high_prices = np.maximum(open_prices, prices) * (1 + np.abs(np.random.normal(0, 0.004, n)))
        low_prices = np.minimum(open_prices, prices) * (1 - np.abs(np.random.normal(0, 0.004, n)))
        volumes = np.random.randint(500_000, 5_000_000, n)

        df = pd.DataFrame({
            "open": open_prices,
            "high": high_prices,
            "low": low_prices,
            "close": prices,
            "volume": volumes
        }, index=dates)
        df.index.name = "datetime"
        return df

    @staticmethod
    def _generate_trading_dates(n_days: int) -> list:
        """生成交易日序列（跳过周末）"""
        dates = []
        current = datetime(2022, 1, 1)
        while len(dates) < n_days:
            if current.weekday() < 5:  # 周一到周五
                dates.append(current)
            current += timedelta(days=1)
        return dates

    @staticmethod
    def _download_real_data(symbol: str) -> pd.DataFrame:
        """
        从yfinance下载真实行情数据
        注意：国内网络可能受限，失败时回退到模拟数据
        """
        try:
            import yfinance as yf
            df = yf.download(
                symbol,
                start=CONFIG.data.start_date,
                end=CONFIG.data.end_date,
                progress=False
            )
            if df.empty:
                raise ValueError("下载数据为空")
            # 统一列名为小写
            df.columns = [c.lower() for c in df.columns]
            return df
        except Exception as e:
            print(f"[警告] 真实数据下载失败: {e}，回退使用模拟数据")
            return DataLoader()._generate_simulated_data()

    @staticmethod
    def calculate_returns(prices: pd.Series) -> pd.Series:
        """计算日收益率"""
        return prices.pct_change().dropna()

    @staticmethod
    def calculate_log_returns(prices: pd.Series) -> pd.Series:
        """计算对数收益率"""
        return np.log(prices / prices.shift(1)).dropna()
