"""
主入口脚本
一键运行完整量化回测流程：
1. 加载数据
2. 单策略回测（双均线，默认参数）
3. 多策略对比（双均线 vs MACD vs 布林带）
4. 交易归因分析
5. 生成可视化图表
6. 输出绩效报告

使用方式：
    python main.py
"""
import os
import sys

# 确保项目根目录在Python路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src import (
    DataLoader, BacktestEngine, TradeAnalyzer, Visualizer, PerformanceMetrics
)
from config.settings import CONFIG


def main():
    print("=" * 60)
    print("       ETF量化策略回测系统 - 完整流程启动")
    print("=" * 60)

    # ========== 1. 数据加载 ==========
    print("\n[1/5] 加载行情数据...")
    loader = DataLoader()
    data = loader.load(use_sim=True)
    print(f"  数据区间: {data.index[0].date()} ~ {data.index[-1].date()}")
    print(f"  数据条数: {len(data)} 个交易日")
    print(f"  价格范围: {data['close'].min():.3f} ~ {data['close'].max():.3f}")

    # ========== 2. 单策略回测（双均线） ==========
    print("\n[2/5] 双均线策略回测（默认参数 5/20）...")
    engine = BacktestEngine()
    result = engine.run_single(data, "DualMA", {"fast_period": 5, "slow_period": 20})
    engine.print_result(result)

    # ========== 3. 交易归因分析 ==========
    print("\n[3/5] 交易归因分析...")
    analyzer = TradeAnalyzer(result["trade_log"])
    print(analyzer.full_report())

    # ========== 4. 多策略对比 ==========
    print("\n[4/5] 多策略对比回测...")
    strategy_list = [
        ("DualMA", {"fast_period": 5, "slow_period": 20}),
        ("MACDStrategy", None),
        ("BollingerStrategy", None),
    ]
    comparison_df, equity_dict = engine.run_comparison(data, strategy_list)
    engine.print_comparison(comparison_df)

    # ========== 5. 可视化 ==========
    print("\n[5/5] 生成可视化图表...")
    viz = Visualizer()

    # 净值曲线对比
    equity_path = viz.plot_equity_curves(equity_dict)
    print(f"  净值曲线对比图: {equity_path}")

    # 双均线回撤图
    dd_path = viz.plot_drawdown(result["equity_curve"], "双均线策略(5/20)")
    print(f"  回撤分析图: {dd_path}")

    # 月度盈亏图
    if not analyzer.df.empty:
        pnl_path = viz.plot_monthly_pnl(analyzer.df)
        if pnl_path:
            print(f"  月度盈亏图: {pnl_path}")

    # 保存绩效对比表
    comparison_path = os.path.join(CONFIG.output_dir, "strategy_comparison.csv")
    comparison_df.to_csv(comparison_path, encoding="utf-8-sig")
    print(f"  策略对比表: {comparison_path}")

    # 保存交易明细
    if not analyzer.df.empty:
        trade_path = os.path.join(CONFIG.output_dir, "trade_details.csv")
        analyzer.to_dataframe().to_csv(trade_path, index=False, encoding="utf-8-sig")
        print(f"  交易明细表: {trade_path}")

    print("\n" + "=" * 60)
    print("       回测流程全部完成！结果已保存至 output/ 目录")
    print("=" * 60)


if __name__ == "__main__":
    main()
