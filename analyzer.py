import ccxt
import pandas as pd
import numpy as np
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class CryptoAnalyzer:
    def __init__(self):
        self.exchange = ccxt.kucoin({'enableRateLimit': True})

    def fetch_ohlcv(self, symbol, timeframe, limit=300):
        pair = f"{symbol}/USDT"
        ohlcv = self.exchange.fetch_ohlcv(pair, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df

    # ── Indicators ──
    def calc_rsi(self, close, period=14):
        delta = close.diff()
        gain = delta.clip(lower=0).rolling(period).mean()
        loss = (-delta.clip(upper=0)).rolling(period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def calc_macd(self, close):
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9, adjust=False).mean()
        return macd, signal, macd - signal

    def calc_bollinger(self, close, period=20):
        sma = close.rolling(period).mean()
        std = close.rolling(period).std()
        return sma + 2*std, sma, sma - 2*std

    def calc_ema(self, close, period):
        return close.ewm(span=period, adjust=False).mean()

    def calc_atr(self, df, period=14):
        high, low, close = df['high'], df['low'], df['close']
        tr = pd.concat([
            high - low,
            (high - close.shift()).abs(),
            (low - close.shift()).abs()
        ], axis=1).max(axis=1)
        return tr.rolling(period).mean()

    # ── Fibonacci ──
    def calc_fibonacci(self, df, lookback=100):
        recent = df.tail(lookback)
        high = recent['high'].max()
        low = recent['low'].min()
        diff = high - low
        levels = {
            '0.0%': high, '23.6%': high - 0.236*diff,
            '38.2%': high - 0.382*diff, '50.0%': high - 0.500*diff,
            '61.8%': high - 0.618*diff, '78.6%': high - 0.786*diff,
            '100%': low, '127.2%': low - 0.272*diff, '161.8%': low - 0.618*diff,
        }
        return levels, high, low

    # ── Support & Resistance (Advanced) ──
    def find_support_resistance(self, df, window=10):
        highs, lows = df['high'].values, df['low'].values
        resistances, supports = [], []
        for i in range(window, len(df) - window):
            if highs[i] == max(highs[i-window:i+window]):
                resistances.append(highs[i])
            if lows[i] == min(lows[i-window:i+window]):
                supports.append(lows[i])
        price = df['close'].iloc[-1]
        resistances = sorted(set([round(r, 6) for r in resistances if r > price]))[:4]
        supports = sorted(set([round(s, 6) for s in supports if s < price]), reverse=True)[:4]
        return supports, resistances

    def find_key_levels(self, df):
        """Find key price levels with strength scores"""
        price = df['close'].iloc[-1]
        atr = self.calc_atr(df).iloc[-1]
        tolerance = atr * 0.5

        all_levels = list(df['high'].tail(100)) + list(df['low'].tail(100))
        level_counts = {}

        for level in all_levels:
            rounded = round(level / tolerance) * tolerance
            level_counts[rounded] = level_counts.get(rounded, 0) + 1

        strong_levels = [(lvl, cnt) for lvl, cnt in level_counts.items() if cnt >= 3]
        strong_levels.sort(key=lambda x: x[1], reverse=True)

        key_supports = sorted([(l, c) for l, c in strong_levels if l < price], key=lambda x: x[0], reverse=True)[:3]
        key_resistances = sorted([(l, c) for l, c in strong_levels if l > price], key=lambda x: x[0])[:3]

        return key_supports, key_resistances

    # ── Price Targets ──
    def calc_price_targets(self, df, supports, resistances, trend_type, fib_levels):
        price = df['close'].iloc[-1]
        atr = self.calc_atr(df).iloc[-1]
        volume = df['volume'].tail(20)
        avg_vol = volume.mean()
        last_vol = volume.iloc[-1]
        vol_ratio = last_vol / avg_vol if avg_vol > 0 else 1

        targets = {
            'bull_targets': [],
            'bear_targets': [],
            'scenarios': [],
            'key_breaks': [],
        }

        # ── Bull targets ──
        bull_targets = []
        for r in resistances[:3]:
            dist_pct = round((r - price) / price * 100, 2)
            bull_targets.append({'price': r, 'pct': dist_pct, 'type': 'resistance'})

        fib_bull = [(n, p) for n, p in fib_levels.items() if p > price and p < price * 1.5]
        for name, fp in sorted(fib_bull, key=lambda x: x[1])[:2]:
            dist_pct = round((fp - price) / price * 100, 2)
            bull_targets.append({'price': round(fp, 6), 'pct': dist_pct, 'type': f'Fib {name}'})

        targets['bull_targets'] = sorted(bull_targets, key=lambda x: x['price'])[:4]

        # ── Bear targets ──
        bear_targets = []
        for s in supports[:3]:
            dist_pct = round((price - s) / price * 100, 2)
            bear_targets.append({'price': s, 'pct': -dist_pct, 'type': 'support'})

        fib_bear = [(n, p) for n, p in fib_levels.items() if p < price and p > price * 0.5]
        for name, fp in sorted(fib_bear, key=lambda x: x[1], reverse=True)[:2]:
            dist_pct = round((price - fp) / price * 100, 2)
            bear_targets.append({'price': round(fp, 6), 'pct': -dist_pct, 'type': f'Fib {name}'})

        targets['bear_targets'] = sorted(bear_targets, key=lambda x: x['price'], reverse=True)[:4]

        # ── Breakout/Breakdown scenarios ──
        if supports:
            s1 = supports[0]
            # If support breaks, next targets
            next_supports = supports[1:] if len(supports) > 1 else []
            fib_below = sorted([(n, p) for n, p in fib_levels.items() if p < s1], key=lambda x: x[1], reverse=True)

            scenario_bear = {
                'trigger': s1,
                'trigger_pct': round((price - s1) / price * 100, 2),
                'description': f'اگر حمایت {s1:,.4f} بشکند',
                'targets': [],
            }
            if next_supports:
                scenario_bear['targets'].append({'price': next_supports[0], 'label': 'حمایت بعدی'})
            if fib_below:
                scenario_bear['targets'].append({'price': round(fib_below[0][1], 6), 'label': f'Fib {fib_below[0][0]}'})
            # Estimated drop
            if next_supports:
                drop_pct = round((s1 - next_supports[0]) / s1 * 100, 2)
                scenario_bear['drop_estimate'] = drop_pct
            targets['scenarios'].append(('bear', scenario_bear))

        if resistances:
            r1 = resistances[0]
            next_resistances = resistances[1:] if len(resistances) > 1 else []
            fib_above = sorted([(n, p) for n, p in fib_levels.items() if p > r1], key=lambda x: x[1])

            scenario_bull = {
                'trigger': r1,
                'trigger_pct': round((r1 - price) / price * 100, 2),
                'description': f'اگر مقاومت {r1:,.4f} بشکند',
                'targets': [],
            }
            if next_resistances:
                scenario_bull['targets'].append({'price': next_resistances[0], 'label': 'مقاومت بعدی'})
            if fib_above:
                scenario_bull['targets'].append({'price': round(fib_above[0][1], 6), 'label': f'Fib {fib_above[0][0]}'})
            if next_resistances:
                pump_pct = round((next_resistances[0] - r1) / r1 * 100, 2)
                scenario_bull['pump_estimate'] = pump_pct
            targets['scenarios'].append(('bull', scenario_bull))

        return targets

    # ── Candlestick Patterns ──
    def detect_patterns(self, df):
        patterns = []
        c = df.tail(5).copy().reset_index(drop=True)
        if len(c) < 3:
            return patterns

        def body(i): return abs(c['close'][i] - c['open'][i])
        def upper_shadow(i): return c['high'][i] - max(c['close'][i], c['open'][i])
        def lower_shadow(i): return min(c['close'][i], c['open'][i]) - c['low'][i]
        def is_bull(i): return c['close'][i] > c['open'][i]
        def is_bear(i): return c['close'][i] < c['open'][i]
        last = len(c) - 1

        if body(last) <= 0.1 * (c['high'][last] - c['low'][last]):
            patterns.append(("Doji", "⚪", "خنثی"))
        if lower_shadow(last) >= 2*body(last) and upper_shadow(last) <= 0.3*body(last) and is_bull(last):
            patterns.append(("Hammer", "🔨", "صعودی - برگشت از کف"))
        if upper_shadow(last) >= 2*body(last) and lower_shadow(last) <= 0.3*body(last) and is_bear(last):
            patterns.append(("Shooting Star", "⭐", "نزولی - برگشت از سقف"))
        if last >= 1:
            if is_bull(last) and is_bear(last-1) and c['close'][last] > c['open'][last-1] and c['open'][last] < c['close'][last-1]:
                patterns.append(("Bullish Engulfing", "📈", "صعودی قوی"))
            elif is_bear(last) and is_bull(last-1) and c['close'][last] < c['open'][last-1] and c['open'][last] > c['close'][last-1]:
                patterns.append(("Bearish Engulfing", "📉", "نزولی قوی"))
        if last >= 2:
            if is_bear(last-2) and body(last-1) < 0.3*body(last-2) and is_bull(last) and c['close'][last] > (c['open'][last-2]+c['close'][last-2])/2:
                patterns.append(("Morning Star", "🌅", "صعودی قوی از کف"))
            if is_bull(last-2) and body(last-1) < 0.3*body(last-2) and is_bear(last) and c['close'][last] < (c['open'][last-2]+c['close'][last-2])/2:
                patterns.append(("Evening Star", "🌆", "نزولی قوی از سقف"))
        if is_bull(last) and upper_shadow(last) < 0.05*body(last) and lower_shadow(last) < 0.05*body(last) and body(last) > 0.7*(c['high'][last]-c['low'][last]):
            patterns.append(("Bullish Marubozu", "💚", "صعودی قوی"))
        if is_bear(last) and upper_shadow(last) < 0.05*body(last) and lower_shadow(last) < 0.05*body(last) and body(last) > 0.7*(c['high'][last]-c['low'][last]):
            patterns.append(("Bearish Marubozu", "❤️", "نزولی قوی"))
        if last >= 2:
            if all(is_bull(i) for i in [last, last-1, last-2]) and c['close'][last] > c['close'][last-1] > c['close'][last-2]:
                patterns.append(("Three White Soldiers", "🪖", "صعودی قوی"))
            if all(is_bear(i) for i in [last, last-1, last-2]) and c['close'][last] < c['close'][last-1] < c['close'][last-2]:
                patterns.append(("Three Black Crows", "🐦‍⬛", "نزولی قوی"))

        return patterns

    # ── Trend ──
    def determine_trend(self, df):
        close = df['close']
        ema20 = self.calc_ema(close, 20).iloc[-1]
        ema50 = self.calc_ema(close, 50).iloc[-1]
        ema200 = self.calc_ema(close, 200).iloc[-1]
        price = close.iloc[-1]
        count = sum([price > ema20, price > ema50, price > ema200, ema20 > ema50, ema50 > ema200])
        if count >= 4: return "صعودی قوی 📈", "bullish"
        elif count == 3: return "صعودی ضعیف 📈", "mild_bullish"
        elif count == 2: return "خنثی ↔️", "neutral"
        elif count == 1: return "نزولی ضعیف 📉", "mild_bearish"
        else: return "نزولی قوی 📉", "bearish"

    # ── Signal Score ──
    def compute_signal(self, df, patterns, trend_type):
        close = df['close']
        price = close.iloc[-1]
        rsi = self.calc_rsi(close).iloc[-1]
        macd, signal, hist = self.calc_macd(close)
        bb_upper, bb_mid, bb_lower = self.calc_bollinger(close)

        long_score = short_score = 0
        if rsi < 30: long_score += 3
        elif rsi < 45: long_score += 1
        elif rsi > 70: short_score += 3
        elif rsi > 55: short_score += 1

        if macd.iloc[-1] > signal.iloc[-1] and hist.iloc[-1] > 0: long_score += 2
        elif macd.iloc[-1] < signal.iloc[-1] and hist.iloc[-1] < 0: short_score += 2

        if price < bb_lower.iloc[-1]: long_score += 2
        elif price > bb_upper.iloc[-1]: short_score += 2

        trend_map = {"bullish": (3,0), "mild_bullish": (1,0), "neutral": (0,0), "mild_bearish": (0,1), "bearish": (0,3)}
        ls, ss = trend_map.get(trend_type, (0,0))
        long_score += ls; short_score += ss

        bull_p = ["Hammer","Bullish Engulfing","Morning Star","Bullish Marubozu","Three White Soldiers"]
        bear_p = ["Shooting Star","Bearish Engulfing","Evening Star","Bearish Marubozu","Three Black Crows"]
        for name, _, _ in patterns:
            if name in bull_p: long_score += 2
            elif name in bear_p: short_score += 2

        return {
            'long_score': long_score, 'short_score': short_score,
            'rsi': rsi, 'macd': macd.iloc[-1], 'signal': signal.iloc[-1],
            'histogram': hist.iloc[-1], 'bb_upper': bb_upper.iloc[-1],
            'bb_lower': bb_lower.iloc[-1], 'bb_mid': bb_mid.iloc[-1],
        }

    # ── MAIN ANALYZE ──
    def analyze(self, symbol, timeframe):
        df = self.fetch_ohlcv(symbol, timeframe, limit=300)
        price = df['close'].iloc[-1]

        patterns = self.detect_patterns(df)
        trend_label, trend_type = self.determine_trend(df)
        fib_levels, swing_high, swing_low = self.calc_fibonacci(df)
        supports, resistances = self.find_support_resistance(df)
        key_supports, key_resistances = self.find_key_levels(df)
        scores = self.compute_signal(df, patterns, trend_type)
        targets = self.calc_price_targets(df, supports, resistances, trend_type, fib_levels)
        atr = self.calc_atr(df).iloc[-1]

        long_score = scores['long_score']
        short_score = scores['short_score']
        total = long_score + short_score
        long_pct = round(long_score/total*100) if total > 0 else 50
        short_pct = 100 - long_pct

        if long_score > short_score + 3: primary, emoji = "🟢 LONG قوی", "🚀"
        elif long_score > short_score: primary, emoji = "🟡 LONG ضعیف", "📈"
        elif short_score > long_score + 3: primary, emoji = "🔴 SHORT قوی", "📉"
        elif short_score > long_score: primary, emoji = "🟡 SHORT ضعیف", "⬇️"
        else: primary, emoji = "⚪ خنثی", "↔️"

        direction = "LONG" if long_score >= short_score else "SHORT"
        if direction == "LONG":
            entry = price
            tp1 = round(price + 1.5*atr, 6)
            tp2 = round(price + 2.5*atr, 6)
            tp3 = round(price + 4.0*atr, 6)
            sl = round(price - 1.0*atr, 6)
        else:
            entry = price
            tp1 = round(price - 1.5*atr, 6)
            tp2 = round(price - 2.5*atr, 6)
            tp3 = round(price - 4.0*atr, 6)
            sl = round(price + 1.0*atr, 6)

        rr = round(abs(tp2 - entry) / abs(entry - sl), 2) if entry != sl else "N/A"

        tf_names = {"1m":"1 دقیقه","5m":"5 دقیقه","15m":"15 دقیقه","1h":"1 ساعت","4h":"4 ساعت","1d":"روزانه","1w":"هفتگی"}

        lines = [
            f"{'═'*28}",
            f"  {emoji} تحلیل {symbol}USDT  {emoji}",
            f"  تایم‌فریم: {tf_names.get(timeframe, timeframe)}",
            f"{'═'*28}",
            f"",
            f"💰 قیمت: `{price:,.6f}` USDT",
            f"📊 روند: {trend_label}",
            f"",
            f"📡 سیگنال: *{primary}*",
            f"  📈 LONG: {long_pct}%  |  📉 SHORT: {short_pct}%",
            f"",
            f"🎯 *پیشنهاد {direction}:*",
            f"  ✅ ورود:  `{entry:,.6f}`",
            f"  🎯 TP1:  `{tp1:,.6f}`",
            f"  🎯 TP2:  `{tp2:,.6f}`",
            f"  🎯 TP3:  `{tp3:,.6f}`",
            f"  🛑 SL:   `{sl:,.6f}`",
            f"  ⚖️  R/R:  {rr}",
            f"",
        ]

        # ── Support / Resistance with Scenarios ──
        lines += [f"{'─'*28}", f"🧱 *حمایت و مقاومت کلیدی:*", f""]

        if resistances:
            lines.append("  🔴 *مقاومت‌ها:*")
            for i, r in enumerate(resistances[:3]):
                dist = round((r - price) / price * 100, 2)
                strength = "قوی" if i == 0 else "متوسط"
                lines.append(f"    R{i+1}: `{r:,.6f}` (+{dist}%) — {strength}")

        if supports:
            lines.append("")
            lines.append("  🟢 *حمایت‌ها:*")
            for i, s in enumerate(supports[:3]):
                dist = round((price - s) / price * 100, 2)
                strength = "قوی" if i == 0 else "متوسط"
                lines.append(f"    S{i+1}: `{s:,.6f}` (-{dist}%) — {strength}")

        # ── Breakout Scenarios ──
        lines += [f"", f"{'─'*28}", f"🔮 *سناریوهای قیمتی:*", f""]

        for stype, scenario in targets['scenarios']:
            if stype == 'bear':
                lines.append(f"  📉 *سناریو نزولی:*")
                lines.append(f"  اگر `{scenario['trigger']:,.6f}` بشکند:")
                for tgt in scenario['targets']:
                    lines.append(f"    ↘️ {tgt['label']}: `{tgt['price']:,.6f}`")
                if 'drop_estimate' in scenario:
                    lines.append(f"    📏 تخمین ریزش: ~{scenario['drop_estimate']}%")
            else:
                lines.append(f"")
                lines.append(f"  📈 *سناریو صعودی:*")
                lines.append(f"  اگر `{scenario['trigger']:,.6f}` بشکند:")
                for tgt in scenario['targets']:
                    lines.append(f"    ↗️ {tgt['label']}: `{tgt['price']:,.6f}`")
                if 'pump_estimate' in scenario:
                    lines.append(f"    📏 تخمین رشد: ~{scenario['pump_estimate']}%")

        # ── Fibonacci ──
        nearest_fibs = sorted(fib_levels.items(), key=lambda x: abs(x[1]-price))[:4]
        lines += [f"", f"{'─'*28}", f"🌀 *فیبوناچی (نزدیک‌ترین):*"]
        lines.append(f"  📍 High: `{swing_high:,.6f}` | Low: `{swing_low:,.6f}`")
        for lvl_name, lvl_price in nearest_fibs:
            dist = round((lvl_price - price) / price * 100, 2)
            arrow = "⬆️" if lvl_price > price else "⬇️"
            lines.append(f"  {arrow} {lvl_name}: `{lvl_price:,.6f}` ({dist:+.2f}%)")

        # ── Indicators ──
        rsi_emoji = "🔴" if scores['rsi'] > 70 else "🟢" if scores['rsi'] < 30 else "🟡"
        macd_emoji = "🟢" if scores['histogram'] > 0 else "🔴"
        lines += [
            f"", f"{'─'*28}", f"📊 *اندیکاتورها:*",
            f"  {rsi_emoji} RSI(14): `{scores['rsi']:.1f}`",
            f"  {macd_emoji} MACD: `{scores['macd']:.6f}`",
            f"  📶 Histogram: `{scores['histogram']:.6f}`",
            f"  🔼 BB Upper: `{scores['bb_upper']:,.6f}`",
            f"  🔽 BB Lower: `{scores['bb_lower']:,.6f}`",
            f"  📏 ATR(14): `{atr:,.6f}`",
        ]

        # ── Candlestick Patterns ──
        lines += [f"", f"{'─'*28}", f"🕯 *الگوهای کندل:*"]
        if patterns:
            for name, pat_emoji, desc in patterns:
                lines.append(f"  {pat_emoji} {name}: {desc}")
        else:
            lines.append("  ⚪ الگوی خاصی شناسایی نشد")

        lines += [
            f"", f"{'─'*28}",
            f"⚠️ این تحلیل توصیه مالی نیست.",
            f"{'═'*28}",
            f"🕐 {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC",
        ]

        return "\n".join(lines)

