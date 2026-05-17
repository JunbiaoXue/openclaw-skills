#!/usr/bin/env python3
"""002124 天邦食品 - 纯技术分析 (修复中文)"""

import json
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.font_manager import FontProperties
import warnings
warnings.filterwarnings('ignore')

FONT = FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
FONTB = FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc')
plt.rcParams['axes.unicode_minus'] = False

STOCK_CODE = '002124'
COST_PRICE = 3.0083
HOLD_SHARES = 3000

print("=" * 60)
print(f"  {STOCK_CODE} 天邦食品 - 纯技术分析")
print("=" * 60)

# ── 1. 加载数据 ──
all_rows = []
for f in ['raw_data_old.json', 'raw_data.json']:
    with open(f'/home/xjb/work/stock_analysis/{f}') as fp:
        all_rows.extend(json.load(fp))

df = pd.DataFrame(all_rows, columns=['date', 'open', 'close', 'high', 'low', 'volume'])
df['date'] = pd.to_datetime(df['date'])
for col in ['open', 'close', 'high', 'low', 'volume']:
    df[col] = pd.to_numeric(df[col], errors='coerce')
df = df.drop_duplicates(subset='date').sort_values('date').reset_index(drop=True)
print(f"  数据: {len(df)}个交易日 ({df['date'].iloc[0].strftime('%Y-%m-%d')} ~ {df['date'].iloc[-1].strftime('%Y-%m-%d')})")

# ── 2. 技术指标 ──
for p in [5,10,20,30,60,120,250]:
    df[f'MA{p}'] = df['close'].rolling(p).mean()

ema12 = df['close'].ewm(span=12, adjust=False).mean()
ema26 = df['close'].ewm(span=26, adjust=False).mean()
df['DIF'] = ema12 - ema26
df['DEA'] = df['DIF'].ewm(span=9, adjust=False).mean()
df['MACD'] = 2 * (df['DIF'] - df['DEA'])

low9 = df['low'].rolling(9).min()
high9 = df['high'].rolling(9).max()
rsv = ((df['close'] - low9) / (high9 - low9) * 100).fillna(50)
df['K'] = rsv.ewm(com=2, adjust=False).mean()
df['D'] = df['K'].ewm(com=2, adjust=False).mean()
df['J'] = 3*df['K'] - 2*df['D']

for p in [6,12,24]:
    delta = df['close'].diff()
    gain = delta.where(delta>0,0).rolling(p).mean()
    loss = (-delta.where(delta<0,0)).rolling(p).mean()
    df[f'RSI{p}'] = 100 - 100/(1+gain/loss)

df['BOLL_MID'] = df['close'].rolling(20).mean()
df['BOLL_STD'] = df['close'].rolling(20).std()
df['BOLL_UP'] = df['BOLL_MID'] + 2*df['BOLL_STD']
df['BOLL_DN'] = df['BOLL_MID'] - 2*df['BOLL_STD']

df['VOL_MA5'] = df['volume'].rolling(5).mean()
df['VOL_MA10'] = df['volume'].rolling(10).mean()

df['TR'] = np.maximum(df['high']-df['low'], np.maximum(abs(df['high']-df['close'].shift(1)), abs(df['low']-df['close'].shift(1))))
df['ATR14'] = df['TR'].rolling(14).mean()
df['OBV'] = (np.sign(df['close'].diff())*df['volume']).fillna(0).cumsum()

for n in [6,14]:
    hn = df['high'].rolling(n).max()
    ln = df['low'].rolling(n).min()
    df[f'WR{n}'] = (hn-df['close'])/(hn-ln)*-100

pdm = df['high'].diff()
mdm = -df['low'].diff()
pdm = pdm.where((pdm>mdm)&(pdm>0),0)
mdm = mdm.where((mdm>pdm)&(mdm>0),0)
atr14 = df['TR'].rolling(14).mean()
df['PDI'] = 100*pdm.rolling(14).mean()/atr14
df['MDI'] = 100*mdm.rolling(14).mean()/atr14
df['ADX'] = (100*abs(df['PDI']-df['MDI'])/(df['PDI']+df['MDI'])).rolling(14).mean()

recent = df.tail(60)
fib_high = recent['high'].max()
fib_low = recent['low'].min()
fib_levels = {'0%':fib_high, '23.6%':fib_high-(fib_high-fib_low)*0.236,
              '38.2%':fib_high-(fib_high-fib_low)*0.382, '50%':fib_high-(fib_high-fib_low)*0.5,
              '61.8%':fib_high-(fib_high-fib_low)*0.618, '100%':fib_low}

# ── 3. K线形态 ──
last = df.iloc[-1]; prev = df.iloc[-2]
body = abs(last['close']-last['open'])
ushadow = last['high']-max(last['close'],last['open'])
lshadow = min(last['close'],last['open'])-last['low']
tr = last['high']-last['low']
patterns = []
if lshadow>2*body and ushadow<body*0.3 and tr>0: patterns.append("锤子线-看涨")
if ushadow>2*body and lshadow<body*0.3: patterns.append("射击之星-看跌")
if body<tr*0.1 and tr>0: patterns.append("十字星-转折")
if last['close']>last['open'] and prev['close']<prev['open'] and last['close']>prev['open']: patterns.append("看涨吞没")
if last['close']<last['open'] and prev['close']>prev['open'] and last['close']<prev['open']: patterns.append("看跌吞没")

# ── 4. 信号评分 ──
signals = {}
# 均线
s,d = 0,[]
for n,v in [('MA5',last['MA5']),('MA10',last['MA10']),('MA20',last['MA20']),('MA60',last['MA60'])]:
    if not np.isnan(v):
        if last['close']>v: s+=1; d.append(f"价格>{n} 看涨")
        else: s-=1; d.append(f"价格<{n} 看跌")
if not np.isnan(last['MA5']) and not np.isnan(last['MA10']) and not np.isnan(last['MA20']):
    if last['MA5']>last['MA10']>last['MA20']: s+=2; d.append("多头排列")
    elif last['MA5']<last['MA10']<last['MA20']: s-=2; d.append("空头排列")
signals['均线']=(s,d)

s,d = 0,[]
if last['DIF']>last['DEA']: s+=1; d.append("DIF>DEA 看涨")
else: s-=1; d.append("DIF<DEA 看跌")
if last['MACD']>0: s+=1; d.append("红柱")
else: s-=1; d.append("绿柱")
for i in range(-3,0):
    if df.iloc[i]['DIF']>df.iloc[i]['DEA'] and df.iloc[i-1]['DIF']<=df.iloc[i-1]['DEA']:
        s+=2; d.append("近期金叉"); break
    if df.iloc[i]['DIF']<df.iloc[i]['DEA'] and df.iloc[i-1]['DIF']>=df.iloc[i-1]['DEA']:
        s-=2; d.append("近期死叉"); break
signals['MACD']=(s,d)

s,d = 0,[]
if last['J']>80: s-=1; d.append(f"J={last['J']:.0f} 超买")
elif last['J']<20: s+=1; d.append(f"J={last['J']:.0f} 超卖")
else: d.append(f"J={last['J']:.0f} 中性")
if last['K']>last['D']: s+=1; d.append("K>D 看涨")
else: s-=1; d.append("K<D 看跌")
signals['KDJ']=(s,d)

s,d = 0,[]
if last['RSI6']>80: s-=2; d.append(f"RSI6={last['RSI6']:.0f} 超买")
elif last['RSI6']<20: s+=2; d.append(f"RSI6={last['RSI6']:.0f} 超卖")
elif last['RSI6']>50: s+=1; d.append(f"RSI6={last['RSI6']:.0f} 偏多")
else: s-=1; d.append(f"RSI6={last['RSI6']:.0f} 偏空")
signals['RSI']=(s,d)

s,d = 0,[]
if last['close']>last['BOLL_UP']: s-=1; d.append("突破上轨")
elif last['close']<last['BOLL_DN']: s+=1; d.append("跌破下轨")
elif last['close']>last['BOLL_MID']: s+=1; d.append("中轨上方")
else: s-=1; d.append("中轨下方")
signals['布林带']=(s,d)

s,d = 0,[]
if last['WR14']>-20: s-=1; d.append(f"WR={last['WR14']:.0f} 超买")
elif last['WR14']<-80: s+=1; d.append(f"WR={last['WR14']:.0f} 超卖")
else: d.append(f"WR={last['WR14']:.0f} 中性")
signals['WR']=(s,d)

s,d = 0,[]
if last['PDI']>last['MDI']: s+=1; d.append("+DI>-DI 看涨")
else: s-=1; d.append("+DI<-DI 看跌")
d.append(f"ADX={last['ADX']:.0f} {'趋势强' if last['ADX']>25 else '震荡'}")
signals['DMI']=(s,d)

s,d = 0,[]
vr = last['volume']/last['VOL_MA5'] if last['VOL_MA5']>0 else 1
if vr>1.5:
    s += 1 if last['close']>last['open'] else -1
    d.append(f"放量(比={vr:.1f}) {'涨放量' if last['close']>last['open'] else '跌放量'}")
else: d.append(f"量比={vr:.1f}")
signals['成交量']=(s,d)

total = sum(v[0] for v in signals.values())
if total>5: verdict="强烈看多"
elif total>2: verdict="偏多"
elif total>-2: verdict="中性震荡"
elif total>-5: verdict="偏空"
else: verdict="强烈看空"

# ── 5. 画图 ──
print("\n📊 生成图表...")

def set_tick_font(ax, size=8):
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontproperties(FONT)
        label.set_fontsize(size)

fig = plt.figure(figsize=(20, 28))
gs = GridSpec(8, 2, figure=fig, hspace=0.35, wspace=0.3)
plot_df = df.tail(60).copy().reset_index(drop=True)
x = range(len(plot_df))
clrs = ['red' if plot_df.loc[i,'close']>=plot_df.loc[i,'open'] else 'green' for i in x]

# K线+均线+布林
ax1 = fig.add_subplot(gs[0:2, :])
for i in x:
    ax1.plot([i,i],[plot_df.loc[i,'low'],plot_df.loc[i,'high']],color=clrs[i],linewidth=0.8)
    bb = min(plot_df.loc[i,'open'],plot_df.loc[i,'close'])
    bh = max(abs(plot_df.loc[i,'close']-plot_df.loc[i,'open']),0.005)
    ax1.add_patch(plt.Rectangle((i-0.3,bb),0.6,bh,facecolor=clrs[i],edgecolor=clrs[i],linewidth=0.8))
for ma,c in [('MA5','yellow'),('MA10','orange'),('MA20','purple'),('MA60','blue')]:
    ax1.plot(x,plot_df[ma].values,label=ma,color=c,linewidth=1.2,alpha=0.8)
ax1.fill_between(x,plot_df['BOLL_UP'],plot_df['BOLL_DN'],alpha=0.1,color='blue')
ax1.plot(x,plot_df['BOLL_UP'],'b--',linewidth=0.7,alpha=0.5,label='BOLL')
ax1.plot(x,plot_df['BOLL_DN'],'b--',linewidth=0.7,alpha=0.5)
ax1.axhline(COST_PRICE,color='red',linestyle=':',linewidth=1.5,alpha=0.7,label=f'成本{COST_PRICE}')
for lv,pr in fib_levels.items():
    ax1.axhline(pr,color='gray',linestyle=':',linewidth=0.5,alpha=0.4)
    ax1.text(len(x)-1,pr,f' {lv}({pr:.2f})',fontsize=7,color='gray',va='center',fontproperties=FONT)
ticks = list(range(0,len(plot_df),10))
ax1.set_xticks(ticks)
ax1.set_xticklabels([plot_df.loc[i,'date'].strftime('%m-%d') for i in ticks],rotation=45,fontsize=8)
ax1.set_title(f'{STOCK_CODE} K线+均线+布林带',fontproperties=FONTB,fontsize=14)
ax1.legend(loc='upper left',fontsize=8,prop=FONT)
ax1.grid(True,alpha=0.3)
ax1.set_ylabel('价格',fontproperties=FONT)
set_tick_font(ax1)

# 成交量
ax2 = fig.add_subplot(gs[2, :])
ax2.bar(x,plot_df['volume']/10000,color=clrs,alpha=0.7,width=0.6)
ax2.plot(x,plot_df['VOL_MA5']/10000,'orange',lw=1,label='MA5')
ax2.plot(x,plot_df['VOL_MA10']/10000,'blue',lw=1,label='MA10')
ax2.set_title('成交量(万手)',fontproperties=FONTB,fontsize=12)
ax2.legend(loc='upper left',fontsize=8,prop=FONT)
ax2.grid(True,alpha=0.3)
ax2.set_xticks(ticks)
ax2.set_xticklabels([plot_df.loc[i,'date'].strftime('%m-%d') for i in ticks],rotation=45,fontsize=8)
set_tick_font(ax2)

# MACD
ax3 = fig.add_subplot(gs[3, 0])
ax3.plot(x,plot_df['DIF'],'blue',lw=1,label='DIF')
ax3.plot(x,plot_df['DEA'],'orange',lw=1,label='DEA')
mc=['red' if v>=0 else 'green' for v in plot_df['MACD']]
ax3.bar(x,plot_df['MACD'],color=mc,alpha=0.6,width=0.6)
ax3.axhline(0,color='gray',lw=0.5)
ax3.set_title('MACD',fontproperties=FONTB,fontsize=12)
ax3.legend(fontsize=8,prop=FONT); ax3.grid(True,alpha=0.3)
set_tick_font(ax3)

# KDJ
ax4 = fig.add_subplot(gs[3, 1])
ax4.plot(x,plot_df['K'],'blue',label='K')
ax4.plot(x,plot_df['D'],'orange',label='D')
ax4.plot(x,plot_df['J'],'purple',label='J')
ax4.axhline(80,color='r',ls='--',lw=0.5,alpha=0.5)
ax4.axhline(20,color='g',ls='--',lw=0.5,alpha=0.5)
ax4.set_title('KDJ',fontproperties=FONTB,fontsize=12)
ax4.legend(fontsize=8,prop=FONT); ax4.grid(True,alpha=0.3)
set_tick_font(ax4)

# RSI
ax5 = fig.add_subplot(gs[4, 0])
ax5.plot(x,plot_df['RSI6'],'blue',label='RSI6')
ax5.plot(x,plot_df['RSI12'],'orange',label='RSI12')
ax5.plot(x,plot_df['RSI24'],'purple',label='RSI24')
ax5.axhline(80,color='r',ls='--',lw=0.5,alpha=0.5)
ax5.axhline(20,color='g',ls='--',lw=0.5,alpha=0.5)
ax5.axhline(50,color='gray',ls='--',lw=0.5,alpha=0.3)
ax5.set_title('RSI',fontproperties=FONTB,fontsize=12)
ax5.legend(fontsize=8,prop=FONT); ax5.grid(True,alpha=0.3)
set_tick_font(ax5)

# WR
ax6 = fig.add_subplot(gs[4, 1])
ax6.plot(x,plot_df['WR14'],'blue',label='WR14')
ax6.plot(x,plot_df['WR6'],'orange',label='WR6')
ax6.axhline(-20,color='r',ls='--',lw=0.5,alpha=0.5)
ax6.axhline(-80,color='g',ls='--',lw=0.5,alpha=0.5)
ax6.set_title('WR威廉',fontproperties=FONTB,fontsize=12)
ax6.legend(fontsize=8,prop=FONT); ax6.grid(True,alpha=0.3)
set_tick_font(ax6)

# DMI
ax7 = fig.add_subplot(gs[5, 0])
ax7.plot(x,plot_df['PDI'],'green',label='+DI')
ax7.plot(x,plot_df['MDI'],'red',label='-DI')
ax7.plot(x,plot_df['ADX'],'blue',label='ADX')
ax7.axhline(25,color='gray',ls='--',lw=0.5,alpha=0.5)
ax7.set_title('DMI/ADX',fontproperties=FONTB,fontsize=12)
ax7.legend(fontsize=8,prop=FONT); ax7.grid(True,alpha=0.3)
set_tick_font(ax7)

# OBV
ax8 = fig.add_subplot(gs[5, 1])
ax8.plot(x,plot_df['OBV']/10000,'blue')
ax8.set_title('OBV(万)',fontproperties=FONTB,fontsize=12)
ax8.grid(True,alpha=0.3)
set_tick_font(ax8)

# 雷达图
ax9 = fig.add_subplot(gs[6, 0], polar=True)
cats = list(signals.keys())
vals = [signals[k][0] for k in cats]
mx = max(abs(v) for v in vals) if vals and max(abs(v) for v in vals)>0 else 1
nv = [v/mx for v in vals]
angles = np.linspace(0,2*np.pi,len(cats),endpoint=False).tolist()
nv += nv[:1]; angles += angles[:1]
ax9.fill(angles,nv,alpha=0.25,color='blue')
ax9.plot(angles,nv,'o-',lw=1.5,color='blue')
ax9.set_xticks(angles[:-1])
ax9.set_xticklabels(cats,fontproperties=FONT,fontsize=9)
ax9.set_ylim(-1.2,1.2)
ax9.axhline(0,color='gray',lw=0.5)
ax9.set_title('技术信号雷达图\n外=看多 内=看空',fontproperties=FONTB,fontsize=11,pad=15)

# 评分表
ax10 = fig.add_subplot(gs[6, 1])
ax10.axis('off')
tdata = []
for nm,(sc,dt) in signals.items():
    arrow = "+" if sc>0 else ("" if sc==0 else "")
    tdata.append([nm, f"{sc:+d}", dt[0][:12] if dt else ""])
tdata.append(["——","——","——"])
tdata.append(["综合", f"{total:+d}", verdict])
tbl = ax10.table(cellText=tdata,colLabels=['指标','评分','信号'],loc='center',cellLoc='center')
tbl.auto_set_font_size(False); tbl.set_fontsize(10); tbl.scale(1,1.5)
for (row,col),cell in tbl.get_celld().items():
    cell.set_text_props(fontproperties=FONT)
ax10.set_title('信号汇总',fontproperties=FONTB,fontsize=12)

# 持仓报告
ax11 = fig.add_subplot(gs[7, :])
ax11.axis('off')
cur = last['close']
pnl = (cur-COST_PRICE)*HOLD_SHARES
pnl_pct = (cur-COST_PRICE)/COST_PRICE*100
supps = sorted([(n,v) for n,v in [('MA5',last['MA5']),('MA10',last['MA10']),('MA20',last['MA20']),('MA60',last['MA60']),('BOLL下轨',last['BOLL_DN'])] if not np.isnan(v) and v<cur],key=lambda x:x[1],reverse=True)
resists = sorted([(n,v) for n,v in [('MA5',last['MA5']),('MA10',last['MA10']),('MA20',last['MA20']),('MA60',last['MA60']),('BOLL上轨',last['BOLL_UP'])] if not np.isnan(v) and v>cur],key=lambda x:x[1])
sl = cur-2*last['ATR14']; tp = cur+3*last['ATR14']

lines = [
    f"股票: {STOCK_CODE} 天邦食品    日期: {last['date'].strftime('%Y-%m-%d')}",
    f"成本: {COST_PRICE:.4f}    现价: {cur:.2f}    持仓: {HOLD_SHARES}股",
    f"浮动盈亏: {pnl:+.2f}元 ({pnl_pct:+.2f}%)",
    "",
    f"支撑位: {', '.join(f'{n}={v:.2f}' for n,v in supps[:4])}",
    f"阻力位: {', '.join(f'{n}={v:.2f}' for n,v in resists[:4])}",
    f"斐波那契: {', '.join(f'{k}={v:.2f}' for k,v in fib_levels.items())}",
    "",
    f"ATR(14): {last['ATR14']:.3f}    止损: {sl:.2f}    止盈: {tp:.2f}",
    f"综合评分: {total:+d}    判定: {verdict}",
]
info_text = "\n".join(lines)
ax11.text(0.05, 0.95, info_text, transform=ax11.transAxes, fontsize=12,
          fontproperties=FONT, verticalalignment='top', fontfamily='monospace',
          bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

plt.suptitle(f'{STOCK_CODE} 天邦食品 - 纯技术分析报告',fontproperties=FONTB,fontsize=16,y=0.995)
out = '/home/xjb/work/stock_analysis/002124_ta.png'
plt.savefig(out,dpi=150,bbox_inches='tight',facecolor='white')
plt.close()
print(f"✅ 图表已保存: {out}")

# 文字
print(f"\n现价:{cur:.2f} 成本:{COST_PRICE:.4f} 盈亏:{pnl:+.2f}元({pnl_pct:+.2f}%)")
for nm,(sc,dt) in signals.items():
    print(f"  {nm:<6} {sc:+d}  {dt[0]}")
print(f"  {'综合':<6} {total:+d}  {verdict}")
print(f"支撑:{','.join(f'{n}={v:.2f}' for n,v in supps[:3])}")
print(f"阻力:{','.join(f'{n}={v:.2f}' for n,v in resists[:3])}")
print(f"止损:{sl:.2f} 止盈:{tp:.2f}")
if patterns: print(f"K线:{'|'.join(patterns)}")
