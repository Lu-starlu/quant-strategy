"""
参数寻优入口脚本
对双均线策略进行网格搜索，寻找最优参数组合，生成参数热力图。

使用方式：
    python run_optimization.py
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src import DataLoader, BacktestEngine, ParameterOptimizer, Visualizer
from config.settings import CONFIG


def main():
    print("=" * 60)
    print("       双均线策略参数寻优 - 网格搜索")
    print("=" * 60)

    # 加载数据
    print("\n[1/3] 加载行情数据...")
    loader = DataLoader()
    data = loader.load(use_sim=True)
    print(f"  数据条数: {len(data)} 个交易日")

    # 网格搜索
    print("\n[2/3] 执行参数网格搜索...")
    print(f"  快线范围: {CONFIG.strategy.fast_range}")
    print(f"  慢线范围: {CONFIG.strategy.slow_range}")
    engine = BacktestEngine()
    optimizer = ParameterOptimizer(engine)
    search_df = optimizer.grid_search_dual_ma(data, objective="sharpe_ratio")

    if search_df.empty:
        print("  未找到有效参数组合")
        return

    optimizer.print_top_n(search_df, n=10, objective="sharpe_ratio")

    best = optimizer.get_best_params(search_df, objective="sharpe_ratio")
    print(f"\n  ★ 最优参数: 快线={best['fast_period']}, 慢线={best['slow_period']}")
    print(f"    夏普比率: {best['sharpe_ratio']:.4f}")
    print(f"    年化收益: {best['annual_return']:.2f}%")
    print(f"    最大回撤: {best['max_drawdown']:.2f}%")

    # 保存寻优结果
    os.makedirs(CONFIG.output_dir, exist_ok=True)
    save_path = os.path.join(CONFIG.output_dir, "param_search_results.csv")
    search_df.to_csv(save_path, index=False, encoding="utf-8-sig")
    print(f"\n  寻优结果已保存: {save_path}")

    # 生成热力图
    print("\n[3/3] 生成参数热力图...")
    viz = Visualizer()
    pivot = optimizer.pivot_heatmap_data(search_df, value_col="sharpe_ratio")
    heatmap_path = viz.plot_param_heatmap(pivot)
    print(f"  热力图已保存: {heatmap_path}")

    print("\n" + "=" * 60)
    print("       参数寻优完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
