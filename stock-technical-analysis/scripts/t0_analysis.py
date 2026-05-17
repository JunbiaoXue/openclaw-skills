#!/usr/bin/env python3
"""T+0品种技术分析 - 可转债 + 跨境ETF"""

import json
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.font_manager import FontProperties
import warnings, subprocess
warnings.filterwarnings('ignore')

FONT = FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
FONTB = FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc')
plt.rcParams['axes.unicode_minus'] = False

# 目标品种
TARGETS = [
    # 可转债 (sz前缀)
    {"code": "118033", "name": "华特转债", "type": "转债", "prefix": "sz", "highlight": "成交额64亿,换手625%"},
    {"code": "123243", "name": "严牌转债", "type": "转债", "prefix": "sz", "highlight": "成交额45亿,+18%振幅"},
    {"code": "127044", "name": "蒙娜转债", "type": "转债", "prefix": "sz", "highlight": "成交额27亿,换手567%"},
    # 跨境ETF
    {"code": "513050", "name": "中概互联ETF", "type": "ETF", "prefix": "sh", "highlight": "中概互联网龙头"},
    {"code": "513100", "name": "纳指ETF", "type": "ETF", "prefix": "sh", "highlight": "纳斯达克100"},
    {"code": "513330", "name": "恒生互联网ETF", "type": "ETF", "prefix": "sh", "highlight": "恒生互联网科技"},
]

def fetch_kline(prefix, code, days=120):
    """腾讯API获取K线"""
    from datetime import datetime, timedelta
    end = datetime.now().strftime('%Y-%m-%d')
    start = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    url = f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={prefix}{code},day,{start},{end},500,qfq"
    try:
        r = subprocess.run(['curl', '-s', '-H', 'User-Agent: Mozilla/5.0', url], capture_output=True, text=True, timeout=15)
        d = json.loads(r.stdout)
        data_key = f"{prefix}{code}"
        rows = d.get('data',{}).get(data_key,{})
        for k in ['qfqday','day']:
            if k in rows and rows[k]:
                df = pd.DataFrame(rows[k], columns=['date','open','close','high','low','volume'])
                df['date'] = pd.to_datetime(df['date'])
                for c in ['open','close','high','low','volume']:
                    df[c] = pd.to_numeric(df[c], errors='coerce')
                return df.sort_values('date').reset_index(drop=True)
    except Exception as e:
        print(f"  ❌ {code} 获取失败: {e}")
    return None

def calc_indicators(df):
    """计算所有技术指标"""
    # 均线
    for p in [5,10,20,60]:
        df[f'MA{p}'] = df['close'].rolling(p).mean()
    # MACD
    e12 = df['close'].ewm(span=12,adjust=False).mean()
    e26 = df['close'].ewm(span=26,adjust=False).mean()
    df['DIF'] = e12 - e26
    df['DEA'] = df['DIF'].ewm(span=9,adjust=False).mean()
    df['MACD'] = 2*(df['DIF']-df['DEA'])
    # KDJ
    l9 = df['low'].rolling(9).min()
    h9 = df['high'].rolling(9).max()
    rsv = ((df['close']-l9)/(h9-l9)*100).fillna(50)
    df['K'] = rsv.ewm(com=2,adjust=False).mean()
    df['D'] = df['K'].ewm(com=2,adjust=False).mean()
    df['J'] = 3*df['K']-2*df['D']
    # RSI
    for p in [6,12,24]:
        delta = df['close'].diff()
        gain = delta.where(delta>0,0).rolling(p).mean()
        loss = (-delta.where(delta<0,0)).rolling(p).mean()
        df[f'RSI{p}'] = 100-100/(1+gain/loss)
    # 布林带
    df['BMID'] = df['close'].rolling(20).mean()
    df['BSTD'] = df['close'].rolling(20).std()
    df['BUP'] = df['BMID']+2*df['BSTD']
    df['BDN'] = df['BMID']-2*df['BSTD']
    # ATR
    df['TR'] = np.maximum(df['high']-df['low'], np.maximum(abs(df['high']-df['close'].shift(1)), abs(df['low']-df['close'].shift(1))))
    df['ATR14'] = df['TR'].rolling(14).mean()
    return df

def score_signals(df):
    """评分"""
    last = df.iloc[-1]
    signals = {}
    # 均线
    s,d = 0,[]
    for n,v in [('MA5',last['MA5']),('MA10',last['MA10']),('MA20',last['MA20'])]:
        if not np.isnan(v):
            if last['close']>v: s+=1; d.append(f">{n}")
            else: s-=1; d.append(f"<{n}")
    signals['均线']=(s,d)
    # MACD
    s,d = 0,[]
    if last['DIF']>last['DEA']: s+=1; d.append("DIF>DEA")
    else: s-=1; d.append("DIF<DEA")
    if last['MACD']>0: s+=1; d.append("红柱")
    else: s-=1; d.append("绿柱")
    signals['MACD']=(s,d)
    # KDJ
    s,d = 0,[]
    if last['J']>80: s-=1; d.append(f"J={last['J']:.0f}超买")
    elif last['J']<20: s+=1; d.append(f"J={last['J']:.0f}超卖")
    else: d.append(f"J={last['J']:.0f}")
    if last['K']>last['D']: s+=1; d.append("K>D")
    else: s-=1; d.append("K<D")
    signals['KDJ']=(s,d)
    # RSI
    s,d = 0,[]
    if last['RSI6']>80: s-=1; d.append(f"RSI6={last['RSI6']:.0f}超买")
    elif last['RSI6']<20: s+=1; d.append(f"RSI6={last['RSI6']:.0f}超卖")
    elif last['RSI6']>50: s+=1; d.append(f"RSI6={last['RSI6']:.0f}偏多")
    else: s-=1; d.append(f"RSI6={last['RSI6']:.0f}偏空")
    signals['RSI']=(s,d)
    # 布林带
    s,d = 0,[]
    if last['close']>last['BUP']: s-=1; d.append("上轨上方")
    elif last['close']<last['BDN']: s+=1; d.append("下轨下方")
    elif last['close']>last['BMID']: s+=1; d.append("中轨上方")
    else: s-=1; d.append("中轨下方")
    signals['布林']=(s,d)
    total = sum(v[0] for v in signals.values())
    return signals, total

def make_chart(target, df, signals, total, ax_row):
    """为一个品种画图"""
    plot_df = df.tail(40).copy().reset_index(drop=True)
    x = range(len(plot_df))
    clrs = ['red' if plot_df.loc[i,'close']>=plot_df.loc[i,'open'] else 'green' for i in x]
    
    # K线+均线
    ax1 = ax_row[0]
    for i in x:
        ax1.plot([i,i],[plot_df.loc[i,'low'],plot_df.loc[i,'high']],color=clrs[i],linewidth=0.8)
        bb = min(plot_df.loc[i,'open'],plot_df.loc[i,'close'])
        bh = max(abs(plot_df.loc[i,'close']-plot_df.loc[i,'open']),0.001)
        ax1.add_patch(plt.Rectangle((i-0.3,bb),0.6,bh,facecolor=clrs[i],edgecolor=clrs[i],linewidth=0.8))
    for ma,c in [('MA5','yellow'),('MA10','orange'),('MA20','purple')]:
        if ma in plot_df.columns:
            ax1.plot(x,plot_df[ma].values,label=ma,color=c,lw=1,alpha=0.8)
    if 'BUP' in plot_df.columns:
        ax1.fill_between(x,plot_df['BUP'],plot_df['BDN'],alpha=0.08,color='blue')
    ticks = list(range(0,len(plot_df),10))
    ax1.set_xticks(ticks)
    ax1.set_xticklabels([plot_df.loc[i,'date'].strftime('%m-%d') for i in ticks],rotation=45,fontsize=7)
    ax1.set_title(f"{target['name']} ({target['code']}) {target['highlight']}",fontproperties=FONTB,fontsize=11)
    ax1.legend(fontsize=7,prop=FONT,loc='upper left')
    ax1.grid(True,alpha=0.3)
    for lb in ax1.get_xticklabels()+ax1.get_yticklabels():
        lb.set_fontproperties(FONT); lb.set_fontsize(7)
    
    # MACD
    ax2 = ax_row[1]
    ax2.plot(x,plot_df['DIF'],'blue',lw=1,label='DIF')
    ax2.plot(x,plot_df['DEA'],'orange',lw=1,label='DEA')
    mc=['red' if v>=0 else 'green' for v in plot_df['MACD']]
    ax2.bar(x,plot_df['MACD'],color=mc,alpha=0.6,width=0.6)
    ax2.axhline(0,color='gray',lw=0.5)
    ax2.set_title('MACD',fontproperties=FONT,fontsize=9)
    ax2.legend(fontsize=7,prop=FONT); ax2.grid(True,alpha=0.3)
    for lb in ax2.get_xticklabels()+ax2.get_yticklabels():
        lb.set_fontproperties(FONT); lb.set_fontsize(7)
    
    # KDJ
    ax3 = ax_row[2]
    ax3.plot(x,plot_df['K'],'blue',label='K')
    ax3.plot(x,plot_df['D'],'orange',label='D')
    ax3.plot(x,plot_df['J'],'purple',label='J')
    ax3.axhline(80,color='r',ls='--',lw=0.5,alpha=0.5)
    ax3.axhline(20,color='g',ls='--',lw=0.5,alpha=0.5)
    ax3.set_title('KDJ',fontproperties=FONT,fontsize=9)
    ax3.legend(fontsize=7,prop=FONT); ax3.grid(True,alpha=0.3)
    for lb in ax3.get_xticklabels()+ax3.get_yticklabels():
        lb.set_fontproperties(FONT); lb.set_fontsize(7)
    
    # 评分文字
    ax4 = ax_row[3]
    ax4.axis('off')
    last = df.iloc[-1]
    atr = last['ATR14'] if not np.isnan(last['ATR14']) else 0
    sl = last['close']-2*atr
    tp = last['close']+3*atr
    if total>5: v="强烈看多"
    elif total>2: v="偏多"
    elif total>-2: v="中性"
    elif total>-5: v="偏空"
    else: v="强烈看空"
    
    lines = [f"现价: {last['close']:.3f}", f"ATR: {atr:.3f}", f"综合: {total:+d} {v}", ""]
    for nm,(sc,dt) in signals.items():
        lines.append(f"{nm}: {sc:+d} {' '.join(dt)}")
    lines.append("")
    lines.append(f"止损: {sl:.3f}")
    lines.append(f"止盈: {tp:.3f}")
    
    # T+0建议
    lines.append("")
    if total >= 2:
        lines.append("T策略: 回踩买,冲高卖")
    elif total <= -2:
        lines.append("T策略: 反弹卖,急跌接")
    else:
        lines.append("T策略: 震荡做差价")
    
    ax4.text(0.05, 0.95, "\n".join(lines), transform=ax4.transAxes, fontsize=9,
             fontproperties=FONT, verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

# ── 主流程 ──
print("=" * 60)
print("  T+0品种技术分析 - 可转债 + 跨境ETF")
print("=" * 60)

fig = plt.figure(figsize=(20, 6*len(TARGETS)))
gs = GridSpec(len(TARGETS), 4, figure=fig, hspace=0.4, wspace=0.3,
              width_ratios=[3, 1, 1, 1.5])

results = []
for idx, target in enumerate(TARGETS):
    print(f"\n{'─'*40}")
    print(f"📊 {target['name']} ({target['code']}) - {target['type']}")
    
    df = fetch_kline(target['prefix'], target['code'])
    if df is None or len(df) < 20:
        print(f"  ❌ 数据不足，跳过")
        continue
    
    print(f"  数据: {len(df)}天 ({df['date'].iloc[0].strftime('%m-%d')} ~ {df['date'].iloc[-1].strftime('%m-%d')})")
    df = calc_indicators(df)
    signals, total = score_signals(df)
    
    last = df.iloc[-1]
    atr = last['ATR14'] if not np.isnan(last['ATR14']) else 0
    
    if total>5: v="强烈看多"
    elif total>2: v="偏多"
    elif total>-2: v="中性"
    elif total>-5: v="偏空"
    else: v="强烈看空"
    
    results.append({
        'name': target['name'], 'code': target['code'], 'type': target['type'],
        'price': last['close'], 'score': total, 'verdict': v, 'atr': atr,
        'highlight': target['highlight']
    })
    
    for nm,(sc,dt) in signals.items():
        print(f"  {nm}: {sc:+d} {' '.join(dt)}")
    print(f"  综合: {total:+d} {v}")
    
    # 画图
    row_axes = [fig.add_subplot(gs[idx, i]) for i in range(4)]
    make_chart(target, df, signals, total, row_axes)

plt.suptitle('T+0品种技术分析 - 可转债 + 跨境ETF',fontproperties=FONTB,fontsize=16,y=1.01)
out = '/home/xjb/work/stock_analysis/t0_analysis.png'
plt.savefig(out,dpi=150,bbox_inches='tight',facecolor='white')
plt.close()
print(f"\n✅ 图表已保存: {out}")

# 排行
print("\n" + "=" * 60)
print("  T+0品种评分排行")
print("=" * 60)
results.sort(key=lambda x: x['score'], reverse=True)
for i, r in enumerate(results, 1):
    emoji = "🟢" if r['score']>2 else ("🔴" if r['score']<-2 else "⚪")
    print(f"  {i}. {emoji} {r['name']}({r['code']}) 现价:{r['price']:.3f} 评分:{r['score']:+d} {r['verdict']} [{r['type']}]")
