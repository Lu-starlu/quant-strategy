"""
交易日志盈亏归因分析脚本
读取 data/ 目录下的实习交易账表Excel，输出多维度盈亏统计报表到 output/

分析维度：
1. 按标的（ETF代码）统计盈亏
2. 按交易时段（小时）统计盈亏
3. 按日期统计每日盈亏
4. 8月折溢价套利标的现差统计
"""

import pandas as pd
import os
import re
import warnings
warnings.filterwarnings('ignore')

# ========== 路径配置 ==========
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def extract_trades_from_account_sheet(filepath, sheet_name):
    """
    从账表类Excel的单个sheet中提取逐笔交易明细
    适用于账表29.xlsx格式：第4行起为逐笔交易
    返回：DataFrame [日期, 代码, 买入时间, 买入价, 卖出时间, 卖出价, 盈亏, 成交量]
    """
    df = pd.read_excel(filepath, sheet_name=sheet_name, header=None)
    trades = []

    for i in range(4, len(df)):
        row = df.iloc[i].tolist()
        code = row[0] if len(row) > 0 else None
        # 代码列非空且为数字/字符串代码
        if pd.isna(code) or str(code).strip() == '':
            continue
        code_str = str(code).strip()
        # 过滤掉非代码行（如"代码"表头、汇总行）
        if not re.match(r'^\d{5,6}', code_str):
            continue

        buy_time = row[2] if len(row) > 2 and pd.notna(row[2]) else None
        buy_price = row[3] if len(row) > 3 and pd.notna(row[3]) else None
        sell_time = row[6] if len(row) > 6 and pd.notna(row[6]) else None
        sell_price = row[7] if len(row) > 7 and pd.notna(row[7]) else None
        profit = row[10] if len(row) > 10 and pd.notna(row[10]) else None
        volume = row[11] if len(row) > 11 and pd.notna(row[11]) else None

        # 至少要有盈亏或买卖价格
        if profit is None and buy_price is None:
            continue

        trades.append({
            '日期': sheet_name,
            '代码': code_str,
            '买入时间': str(buy_time) if buy_time else '',
            '买入价': float(buy_price) if buy_price is not None else None,
            '卖出时间': str(sell_time) if sell_time else '',
            '卖出价': float(sell_price) if sell_price is not None else None,
            '盈亏': float(profit) if profit is not None else None,
            '成交量': float(volume) if volume is not None else None,
        })

    return trades


def extract_daily_summary(filepath):
    """
    从账表30.xlsx提取每日盈亏汇总（7月份格式）
    返回：DataFrame [日期, 总盈利, 净利润, 总成交量]
    """
    xl = pd.ExcelFile(filepath)
    summaries = []

    for sheet in xl.sheet_names:
        df = pd.read_excel(filepath, sheet_name=sheet, header=None)
        if len(df) < 2:
            continue
        row0 = df.iloc[0].tolist()
        row1 = df.iloc[1].tolist()

        # 判断是否为汇总格式（第0行含"总盈利"或"总券息"）
        header_text = ' '.join([str(x) for x in row0 if pd.notna(x)])
        if '总盈利' not in header_text and '总券息' not in header_text:
            continue

        total_profit = None
        net_profit = None
        volume = None

        # 第1行对应数值
        for idx, cell in enumerate(row1):
            if pd.isna(cell):
                continue
            try:
                val = float(cell)
            except (ValueError, TypeError):
                continue
            # 根据第0行表头判断列含义
            if idx < len(row0) and pd.notna(row0[idx]):
                h = str(row0[idx])
                if '总盈利' in h:
                    total_profit = val
                elif '净利润' in h:
                    net_profit = val
                elif '总成交量' in h:
                    volume = val

        if net_profit is not None or total_profit is not None:
            summaries.append({
                '日期': sheet,
                '总盈利': total_profit,
                '净利润': net_profit if net_profit is not None else total_profit,
                '总成交量': volume,
            })

    return pd.DataFrame(summaries)


def extract_arbitrage_targets(filepath):
    """
    从账表30.xlsx提取8月折溢价套利标的和现差
    返回：DataFrame [日期, ETF标的, 现差, 套利类型]
    """
    xl = pd.ExcelFile(filepath)
    targets = []

    for sheet in xl.sheet_names:
        if not sheet.startswith('2026.08'):
            continue
        df = pd.read_excel(filepath, sheet_name=sheet, header=None)

        etf_name = ''
        xiancha = None

        for i in range(min(20, len(df))):
            row = df.iloc[i].tolist()
            for cell in row:
                if pd.isna(cell):
                    continue
                s = str(cell).strip()
                # 匹配ETF代码+名称（如159801芯片基金、516710新材料50）
                if re.match(r'^\d{5,6}', s) and len(s) > 5:
                    if not etf_name:
                        etf_name = s
                # 匹配现差
                if '现差' in s:
                    m = re.search(r'[-+]?\d+\.?\d*', s)
                    if m:
                        xiancha = float(m.group())

        if etf_name or xiancha is not None:
            targets.append({
                '日期': sheet,
                'ETF标的': etf_name,
                '现差': xiancha,
                '套利类型': '溢价' if (xiancha is not None and xiancha > 0) else ('折价' if xiancha is not None else ''),
            })

    return pd.DataFrame(targets)


def extract_trade_log_text(filepath):
    """
    从交易日志Excel提取每日交易总结文本
    返回：DataFrame [日期, 交易总结, 建仓逻辑]
    """
    xl = pd.ExcelFile(filepath)
    logs = []

    for sheet in xl.sheet_names:
        df = pd.read_excel(filepath, sheet_name=sheet, header=None)
        summary = ''
        logic = ''

        for i in range(len(df)):
            for j in range(len(df.columns)):
                cell = df.iloc[i, j]
                if pd.isna(cell) or not isinstance(cell, str):
                    continue
                text = cell.strip()
                if len(text) < 10:
                    continue
                if '交易总结' in text or '日总结' in text:
                    summary = text[:500]
                elif '建仓逻辑' in text:
                    logic = text[:300]

        if summary or logic:
            logs.append({
                '日期': sheet,
                '交易总结': summary,
                '建仓逻辑': logic,
            })

    return pd.DataFrame(logs)


def main():
    print("=" * 60)
    print("交易日志盈亏归因分析")
    print("=" * 60)

    all_trades = []

    # ========== 1. 提取逐笔交易明细（账表29） ==========
    account_file = os.path.join(DATA_DIR, "账表29.xlsx")
    if os.path.exists(account_file):
        print(f"\n[1/5] 读取逐笔交易明细: {account_file}")
        xl = pd.ExcelFile(account_file)
        for sheet in xl.sheet_names:
            trades = extract_trades_from_account_sheet(account_file, sheet)
            all_trades.extend(trades)
        print(f"  提取到 {len(all_trades)} 笔逐笔交易")
    else:
        print(f"  未找到 {account_file}，跳过逐笔交易提取")

    df_trades = pd.DataFrame(all_trades)

    # ========== 2. 提取每日盈亏汇总（账表30） ==========
    summary_file = os.path.join(DATA_DIR, "账表30.xlsx")
    df_daily = pd.DataFrame()
    if os.path.exists(summary_file):
        print(f"\n[2/5] 读取每日盈亏汇总: {summary_file}")
        df_daily = extract_daily_summary(summary_file)
        print(f"  提取到 {len(df_daily)} 个交易日的盈亏汇总")

    # ========== 3. 提取8月套利标的 ==========
    df_arbitrage = pd.DataFrame()
    if os.path.exists(summary_file):
        print(f"\n[3/5] 读取8月折溢价套利标的")
        df_arbitrage = extract_arbitrage_targets(summary_file)
        print(f"  提取到 {len(df_arbitrage)} 个套利标的记录")

    # ========== 4. 提取交易日志文本 ==========
    log_files = ["交易日志9.xlsx", "交易日志10.xlsx", "交易日志张桐.xlsx"]
    all_logs = []
    for lf in log_files:
        lf_path = os.path.join(DATA_DIR, lf)
        if os.path.exists(lf_path):
            df_log = extract_trade_log_text(lf_path)
            all_logs.append(df_log)
    df_logs = pd.concat(all_logs, ignore_index=True) if all_logs else pd.DataFrame()
    print(f"\n[4/5] 读取交易日志文本: {len(df_logs)} 条记录")

    # ========== 5. 多维度统计分析 ==========
    print(f"\n[5/5] 生成统计报表")

    # --- 5.1 按标的统计盈亏 ---
    if not df_trades.empty and '盈亏' in df_trades.columns:
        df_by_code = df_trades.groupby('代码').agg(
            交易笔数=('盈亏', 'count'),
            总盈亏=('盈亏', 'sum'),
            平均盈亏=('盈亏', 'mean'),
            最大盈利=('盈亏', 'max'),
            最大亏损=('盈亏', 'min'),
            盈利笔数=('盈亏', lambda x: (x > 0).sum()),
            亏损笔数=('盈亏', lambda x: (x < 0).sum()),
        ).reset_index()
        df_by_code['胜率(%)'] = (df_by_code['盈利笔数'] / df_by_code['交易笔数'] * 100).round(1)
        df_by_code = df_by_code.sort_values('总盈亏', ascending=False)
        out_code = os.path.join(OUTPUT_DIR, "profit_by_code.csv")
        df_by_code.to_csv(out_code, index=False, encoding='utf-8-sig')
        print(f"  ✓ 按标的盈亏统计: {out_code}")
        print(df_by_code.to_string(index=False))

    # --- 5.2 按交易时段（小时）统计盈亏 ---
    if not df_trades.empty and '买入时间' in df_trades.columns:
        def extract_hour(t):
            m = re.match(r'(\d{1,2}):', str(t))
            return int(m.group(1)) if m else None

        df_trades['交易小时'] = df_trades['买入时间'].apply(extract_hour)
        df_by_hour = df_trades.dropna(subset=['交易小时']).groupby('交易小时').agg(
            交易笔数=('盈亏', 'count'),
            总盈亏=('盈亏', 'sum'),
            平均盈亏=('盈亏', 'mean'),
            盈利笔数=('盈亏', lambda x: (x > 0).sum()),
        ).reset_index()
        df_by_hour['胜率(%)'] = (df_by_hour['盈利笔数'] / df_by_hour['交易笔数'] * 100).round(1)
        df_by_hour = df_by_hour.sort_values('交易小时')
        out_hour = os.path.join(OUTPUT_DIR, "profit_by_hour.csv")
        df_by_hour.to_csv(out_hour, index=False, encoding='utf-8-sig')
        print(f"\n  ✓ 按时段盈亏统计: {out_hour}")
        print(df_by_hour.to_string(index=False))

    # --- 5.3 按日期统计每日盈亏 ---
    if not df_daily.empty:
        df_daily_sorted = df_daily.sort_values('日期')
        out_daily = os.path.join(OUTPUT_DIR, "profit_by_date.csv")
        df_daily_sorted.to_csv(out_daily, index=False, encoding='utf-8-sig')
        print(f"\n  ✓ 按日期盈亏汇总: {out_daily}")
        print(df_daily_sorted.to_string(index=False))
        # 汇总统计
        total_days = len(df_daily_sorted)
        profit_days = (df_daily_sorted['净利润'] > 0).sum()
        loss_days = (df_daily_sorted['净利润'] < 0).sum()
        total_pnl = df_daily_sorted['净利润'].sum()
        print(f"\n  【每日盈亏汇总统计】")
        print(f"  交易日数: {total_days}, 盈利天数: {profit_days}, 亏损天数: {loss_days}")
        print(f"  净利润总和: {total_pnl:.4f}, 日均盈亏: {total_pnl/total_days:.4f}")

    # --- 5.4 8月套利标的现差统计 ---
    if not df_arbitrage.empty:
        out_arb = os.path.join(OUTPUT_DIR, "arbitrage_targets.csv")
        df_arbitrage.to_csv(out_arb, index=False, encoding='utf-8-sig')
        print(f"\n  ✓ 8月套利标的统计: {out_arb}")
        print(df_arbitrage.to_string(index=False))
        premium_count = (df_arbitrage['套利类型'] == '溢价').sum()
        discount_count = (df_arbitrage['套利类型'] == '折价').sum()
        print(f"\n  【套利类型分布】溢价: {premium_count}次, 折价: {discount_count}次")

    # --- 5.5 逐笔交易明细导出 ---
    if not df_trades.empty:
        out_trades = os.path.join(OUTPUT_DIR, "trade_details_all.csv")
        df_trades.to_csv(out_trades, index=False, encoding='utf-8-sig')
        print(f"\n  ✓ 逐笔交易明细: {out_trades}")

    # --- 5.6 交易日志文本导出 ---
    if not df_logs.empty:
        out_logs = os.path.join(OUTPUT_DIR, "trade_logs_summary.csv")
        df_logs.to_csv(out_logs, index=False, encoding='utf-8-sig')
        print(f"\n  ✓ 交易日志文本汇总: {out_logs}")

    print("\n" + "=" * 60)
    print("分析完成！所有报表已保存至 output/ 目录")
    print("=" * 60)


if __name__ == "__main__":
    main()
