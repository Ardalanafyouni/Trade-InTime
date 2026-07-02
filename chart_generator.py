import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import pandas as pd
import numpy as np
from io import BytesIO
import warnings
warnings.filterwarnings('ignore')

plt.rcParams['figure.facecolor'] = '#131722'
plt.rcParams['axes.facecolor'] = '#131722'
plt.rcParams['axes.edgecolor'] = '#2a2e39'
plt.rcParams['axes.labelcolor'] = '#d1d4dc'
plt.rcParams['xtick.color'] = '#d1d4dc'
plt.rcParams['ytick.color'] = '#d1d4dc'
plt.rcParams['grid.color'] = '#2a2e39'
plt.rcParams['text.color'] = '#d1d4dc'


def generate_chart(df, symbol, timeframe, patterns, trend_label, trend_type, fib_levels, supports, resistances, signal_data):
    df = df.tail(60).copy().reset_index(drop=True)

    fig = plt.figure(figsize=(14, 12))
    gs = gridspec.GridSpec(4, 1, height_ratios=[3, 1, 1, 1], hspace=0.08)

    ax1 = fig.add_subplot(gs[0])
    ax_vol = fig.add_subplot(gs[1], sharex=ax1)
    ax2 = fig.add_subplot(gs[2], sharex=ax1)
    ax3 = fig.add_subplot(gs[3], sharex=ax1)

    # ── Candlesticks ──
    for i, row in df.iterrows():
        color = '#26a69a' if row['close'] >= row['open'] else '#ef5350'
        ax1.plot([i, i], [row['low'], row['high']], color=color, linewidth=0.8)
        body_bottom = min(row['open'], row['close'])
        body_height = abs(row['close'] - row['open'])
        rect = plt.Rectangle((i - 0.3, body_bottom), 0.6, max(body_height, row['close'] * 0.0001),
                              color=color, zorder=3)
        ax1.add_patch(rect)

    # ── EMA lines ──
    close = df['close']
    ema20 = close.ewm(span=20, adjust=False).mean()
    ema50 = close.ewm(span=50, adjust=False).mean()
    ema200 = close.ewm(span=200, adjust=False).mean()

    ax1.plot(range(len(df)), ema20, color='#f0c040', linewidth=1.2, label='EMA20', alpha=0.9)
    ax1.plot(range(len(df)), ema50, color='#2196F3', linewidth=1.2, label='EMA50', alpha=0.9)
    ax1.plot(range(len(df)), ema200, color='#ff6b6b', linewidth=1.2, label='EMA200', alpha=0.9)

    # ── Fibonacci levels ──
    price = df['close'].iloc[-1]
    fib_colors = {'0.0%': '#ffffff', '23.6%': '#ab47bc', '38.2%': '#42a5f5',
                  '50.0%': '#26a69a', '61.8%': '#ffca28', '78.6%': '#ff7043', '100%': '#ffffff'}
    for lvl_name, lvl_price in fib_levels.items():
        if lvl_name in fib_colors:
            color = fib_colors[lvl_name]
            ax1.axhline(y=lvl_price, color=color, linewidth=0.6, linestyle='--', alpha=0.5)
            ax1.text(len(df) - 1, lvl_price, f' Fib {lvl_name}', fontsize=6,
                     color=color, va='center', alpha=0.8)

    # ── Support & Resistance ──
    for s in supports[:2]:
        ax1.axhline(y=s, color='#26a69a', linewidth=1, linestyle=':', alpha=0.7)
    for r in resistances[:2]:
        ax1.axhline(y=r, color='#ef5350', linewidth=1, linestyle=':', alpha=0.7)

    # ── Mark candlestick patterns ──
    bull_patterns = ["Hammer", "Bullish Engulfing", "Morning Star", "Bullish Marubozu", "Three White Soldiers"]
    bear_patterns = ["Shooting Star", "Bearish Engulfing", "Evening Star", "Bearish Marubozu", "Three Black Crows"]
    last_idx = len(df) - 1
    for name, emoji, desc in patterns:
        if name in bull_patterns:
            ax1.annotate('▲', xy=(last_idx, df['low'].iloc[-1]),
                        xytext=(last_idx, df['low'].iloc[-1] * 0.998),
                        color='#26a69a', fontsize=12, ha='center', fontweight='bold')
        elif name in bear_patterns:
            ax1.annotate('▼', xy=(last_idx, df['high'].iloc[-1]),
                        xytext=(last_idx, df['high'].iloc[-1] * 1.002),
                        color='#ef5350', fontsize=12, ha='center', fontweight='bold')

    # ── Signal box ──
    long_score = signal_data['long_score']
    short_score = signal_data['short_score']
    total = long_score + short_score
    long_pct = round(long_score / total * 100) if total > 0 else 50
    short_pct = 100 - long_pct

    if long_score > short_score + 3:
        sig_text = "🟢 LONG STRONG"
        sig_color = '#26a69a'
    elif long_score > short_score:
        sig_text = "🟡 LONG WEAK"
        sig_color = '#ffca28'
    elif short_score > long_score + 3:
        sig_text = "🔴 SHORT STRONG"
        sig_color = '#ef5350'
    elif short_score > long_score:
        sig_text = "🟡 SHORT WEAK"
        sig_color = '#ffca28'
    else:
        sig_text = "⚪ NEUTRAL"
        sig_color = '#90a4ae'

    ax1.text(0.02, 0.97, f"{symbol}/USDT  {timeframe}",
             transform=ax1.transAxes, fontsize=11, fontweight='bold',
             color='#d1d4dc', va='top')
    ax1.text(0.02, 0.90, f"Price: {price:,.4f}",
             transform=ax1.transAxes, fontsize=9, color='#d1d4dc', va='top')
    ax1.text(0.02, 0.84, f"Trend: {trend_label}",
             transform=ax1.transAxes, fontsize=9, color='#d1d4dc', va='top')
    ax1.text(0.98, 0.97, sig_text,
             transform=ax1.transAxes, fontsize=10, fontweight='bold',
             color=sig_color, va='top', ha='right',
             bbox=dict(boxstyle='round,pad=0.3', facecolor='#1e222d', edgecolor=sig_color))
    ax1.text(0.98, 0.88, f"LONG {long_pct}%  |  SHORT {short_pct}%",
             transform=ax1.transAxes, fontsize=8, color='#90a4ae', va='top', ha='right')

    # ── Pattern labels ──
    if patterns:
        pat_text = " | ".join([f"{e} {n}" for n, e, d in patterns[:3]])
        ax1.text(0.5, 0.02, pat_text, transform=ax1.transAxes, fontsize=7,
                 color='#90a4ae', ha='center', va='bottom')

    ax1.legend(loc='upper center', fontsize=7, ncol=3, framealpha=0.3,
               facecolor='#1e222d', edgecolor='#2a2e39')
    ax1.grid(True, alpha=0.2)
    ax1.set_ylabel('Price', fontsize=8)
    plt.setp(ax1.get_xticklabels(), visible=False)

    # ── Volume ──
    volume = df['volume']
    vol_colors = ['#26a69a' if row['close'] >= row['open'] else '#ef5350' for _, row in df.iterrows()]
    ax_vol.bar(range(len(df)), volume, color=vol_colors, alpha=0.8, width=0.8)

    vol_ma = volume.rolling(20).mean()
    ax_vol.plot(range(len(df)), vol_ma, color='#f0c040', linewidth=1.1, label='Vol MA20', alpha=0.9)

    avg_vol = vol_ma.iloc[-1] if not pd.isna(vol_ma.iloc[-1]) else volume.mean()
    last_vol = volume.iloc[-1]
    vol_ratio = last_vol / avg_vol if avg_vol > 0 else 1
    vol_tag = "🔥 SPIKE" if vol_ratio >= 2 else "HIGH" if vol_ratio >= 1.3 else "LOW" if vol_ratio <= 0.5 else ""
    vol_tag_color = '#ff6b6b' if vol_ratio >= 2 else '#26a69a' if vol_ratio >= 1.3 else '#90a4ae' if vol_ratio <= 0.5 else '#d1d4dc'
    ax_vol.text(0.02, 0.85, f"Vol: {last_vol:,.0f}  ({vol_ratio:.1f}x)  {vol_tag}",
                transform=ax_vol.transAxes, fontsize=7.5, color=vol_tag_color,
                va='top', fontweight='bold')

    ax_vol.set_ylabel('Volume', fontsize=8)
    ax_vol.grid(True, alpha=0.2)
    ax_vol.legend(loc='upper right', fontsize=6.5, framealpha=0.3, facecolor='#1e222d')
    plt.setp(ax_vol.get_xticklabels(), visible=False)

    # ── RSI ──
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    ax2.plot(range(len(df)), rsi, color='#ce93d8', linewidth=1.2, label='RSI(14)')
    ax2.axhline(y=70, color='#ef5350', linewidth=0.7, linestyle='--', alpha=0.7)
    ax2.axhline(y=30, color='#26a69a', linewidth=0.7, linestyle='--', alpha=0.7)
    ax2.fill_between(range(len(df)), rsi, 70, where=(rsi >= 70), alpha=0.2, color='#ef5350')
    ax2.fill_between(range(len(df)), rsi, 30, where=(rsi <= 30), alpha=0.2, color='#26a69a')
    ax2.set_ylim(0, 100)
    ax2.set_ylabel('RSI', fontsize=8)
    ax2.grid(True, alpha=0.2)
    ax2.legend(loc='upper left', fontsize=7, framealpha=0.3, facecolor='#1e222d')
    plt.setp(ax2.get_xticklabels(), visible=False)

    # ── MACD ──
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal_line = macd.ewm(span=9, adjust=False).mean()
    histogram = macd - signal_line

    colors = ['#26a69a' if h >= 0 else '#ef5350' for h in histogram]
    ax3.bar(range(len(df)), histogram, color=colors, alpha=0.7, width=0.8)
    ax3.plot(range(len(df)), macd, color='#2196F3', linewidth=1.2, label='MACD')
    ax3.plot(range(len(df)), signal_line, color='#ff9800', linewidth=1.2, label='Signal')
    ax3.axhline(y=0, color='#90a4ae', linewidth=0.5)
    ax3.set_ylabel('MACD', fontsize=8)
    ax3.grid(True, alpha=0.2)
    ax3.legend(loc='upper left', fontsize=7, framealpha=0.3, facecolor='#1e222d')

    # ── X axis labels ──
    step = max(1, len(df) // 8)
    tick_positions = range(0, len(df), step)
    tick_labels = [df['timestamp'].iloc[i].strftime('%m/%d %H:%M') for i in tick_positions]
    ax3.set_xticks(list(tick_positions))
    ax3.set_xticklabels(tick_labels, fontsize=6, rotation=30)

    plt.suptitle(f"{symbol}/USDT — {timeframe} Chart Analysis",
                 fontsize=12, fontweight='bold', color='#d1d4dc', y=0.98)

    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=130, bbox_inches='tight',
                facecolor='#131722', edgecolor='none')
    buf.seek(0)
    plt.close(fig)
    return buf


