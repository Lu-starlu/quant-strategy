# ETF量化实践项目 — 实习成果落地
> 数据科学与大数据技术 | 实习项目
仓库地址：https://github.com/Lu-starlu/quant-strategy

## 项目概述
本项目基于量化实习期间学习的ETF套利机制、策略回测、交易分析流程，使用Python完成一套完整迷你量化实践。
将实习中的模拟交易经验转化为可复现代码，包含策略回测、交易日志盈亏归因、实习复盘三部分，完整覆盖从策略实现到结果分析全流程。

## 目录结构
├── strategy.py        # Backtrader 双均线 ETF 策略回测
├── trade_analysis.py  # Pandas 交易日志盈亏多维度归因
└── intern_report.md   # 实习复盘笔记：ETF 套利、回测流程、实盘与回测差异

## 项目模块说明
### 1. ETF双均线策略回测 strategy.py
- 基于Backtrader搭建回测框架，实现短/长均线金叉死叉交易逻辑
- 输出标准化量化指标：总收益率、年化收益率、最大回撤、夏普比率
- 加入交易手续费模拟，贴近真实交易成本

### 2. 交易日志盈亏归因 trade_analysis.py
- 使用Pandas对交易记录做统计分析
- 从标的、交易时段两个维度做盈亏拆解
- 统计盈利/亏损分布，定位策略优势与缺陷

### 3. 实习复盘文档 intern_report.md
- ETF折溢价套利原理、申赎交易逻辑
- 量化策略完整测试工作流程
- 回测与实盘之间差距：滑点、流动性、申赎时延、手续费影响

## 技术栈
`Python3` | `Backtrader` | `Pandas` | `NumPy`

## ▶运行方式
```bash
# 安装依赖
pip install backtrader pandas numpy

# 运行策略回测
python strategy.py

# 运行交易日志归因分析
python trade_analysis.py
