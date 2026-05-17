---
name: stock-technical-analysis
description: A股股票技术分析+基本面多源验证，短线交易建议。腾讯API获取K线数据，8指标技术分析，中文图表。
version: 1.0.0
tags: [stock, technical-analysis, trading, a-share, short-term]
---

# 股票技术分析 Skill

对A股股票进行纯技术分析 + 基本面多源验证，输出短线买卖建议和中文图表。

## 核心流程

### 1. 获取K线数据（腾讯API）

东方财富API被屏蔽，**必须用腾讯股票API**：

```bash
curl -s -H "User-Agent: Mozilla/5.0" \
  "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sz{CODE},day,{START},{END},500,qfq"
```

- 不要设置代理（国内站）
- 股票代码：60开头=sh，00/30开头=sz

### 2. 基本面多源验证（必须）

至少3次搜索交叉验证：
```python
search_queries = [
    f"{stock_code} {company_name} 最新财报 业绩",
    f"{stock_code} {company_name} 公告 重整 风险",
    f"{stock_code} {company_name} 股价 最新消息 本周",
]
```

### 3. 技术指标（8个系统）

| 指标 | 参数 | 信号逻辑 |
|------|------|----------|
| 均线 | MA5/10/20/60 | 多头/空头排列 |
| MACD | 12/26/9 | 金叉/死叉、红绿柱 |
| KDJ | 9/3/3 | J值超买(>80)/超卖(<20) |
| RSI | 6/12/24 | 偏多/偏空 |
| 布林带 | 20日/2倍标准差 | 上轨/中轨/下轨 |
| WR威廉 | 6/14 | 超买/超卖 |
| DMI/ADX | 14 | 趋势方向和强度 |
| 成交量 | VOL MA5/10 | 放量/缩量 |

### 4. 中文字体（关键）

```python
from matplotlib.font_manager import FontProperties
FONT = FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
FONTB = FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc')
# 所有中文用 fontproperties=FONT
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `scripts/tech_analysis_v3.py` | 单股技术分析（8指标+雷达图+评分） |
| `scripts/t0_analysis.py` | T+0品种批量分析（可转债+跨境ETF） |
| `scripts/002124_ta.png` | 天邦食品分析示例图表 |
| `scripts/t0_analysis.png` | T+0品种分析示例图表 |

## 评分规则

每个指标 -4 到 +4 分：
- > +5: 强烈看多 | > +2: 偏多 | -2~+2: 中性 | < -2: 偏空 | < -5: 强烈看空

## Pitfalls

1. 东方财富API不通 → 用腾讯API
2. 字体方框 → 用 FontProperties(fname=...) 不用 rcParams
3. 基本面只搜一次 → 必须多源交叉验证
4. K线形态 total_range=0 → 除零检查
