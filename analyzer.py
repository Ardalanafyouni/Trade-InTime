import ccxt
import pandas as pd
import numpy as np
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class CryptoAnalyzer:
    def __init__(self):
        self.exchange = ccxt.binance({
            'enableRateLimit': True,
        })

    def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int = 200):
        """Fetch OHLCV data from Binance"""
        pair = f"{symbol}/USDT"
        ohlcv = self.exchange.fetch_ohlcv(pair, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df

    # ─────────────────────────────────────────────
    # INDICATORS
    # ─────────────────────────────────────────────

    def calc_rsi(self, close: pd.Series, period: int = 14) -> pd.Series:
        delta = close.diff()
        gain = delta.clip(lower=0).rolling(period).mean()
        loss = (-delta.clip(upper=0)).rolling(period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def calc_macd(self, close: pd.Series):
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9, adjust=False).mean()
        histogram = macd - signal
        return macd, signal, histogram

    def calc_bollinger(self, close: pd.Series, period: int = 20):
        sma = close.rolling(period).mean()
        std = close.rolling(period).std()
        upper = sma + (2 * std)
        lower = sma - (2 * std)
        return upper, sma, lower

    def calc_ema(self, close: pd.Series, period: int) -> pd.Series:
        return close.ewm(span=period, adjust=False).mean()

    # ─────────────────────────────────────────────
    # FIBONACCI LEVELS
    # ─────────────────────────────────────────────

    def calc_fibonacci(self, df: pd.DataFrame, lookback: int = 50):
        recent = df.tail(lookback)
        high = recent['high'].max()
        low = recent['low'].min()
        diff = high - low

        levels = {
            '0.0%': high,
            '23.6%': high - 0.236 * diff,
            '38.2%': high - 0.382 * diff,
            '50.0%': high - 0.500 * diff,
            '61.8%': high - 0.618 * diff,
            '78.6%': high - 0.786 * diff,
            '100%': low,
            '127.2%': low - 0.272 * diff,
            '161.8%': low - 0.618 * diff,
        }
        return levels, high, low

    def nearest_fib_levels(self, price: float, fib_levels: dict, n: int = 3):
        """Find nearest Fibonacci support/resistance levels"""
        sorted_levels = sorted(fib_levels.items(), key=lambda x: abs(x[1] - price))
        return sorted_levels[:n]

    # ─────────────────────────────────────────────
    # CANDLESTICK PATTERNS
    # ─────────────────────────────────────────────

    def detect_patterns(self, df: pd.DataFrame) -> list:
        patterns = []
        c = df.tail(5).copy()
        c = c.reset_index(drop=True)

        if len(c) < 3:
            return patterns

        def body(i): return abs(c['close'][i] - c['open'][i])
        def upper_shadow(i): return c['high'][i] - max(c['close'][i], c['open'][i])
        def lower_shadow(i): return min(c['close'][i], c['open'][i]) - c['low'][i]
        def is_bull(i): return c['close'][i] > c['open'][i]
        def is_bear(i): return c['close'][i] < c['open'][i]

        last = len(c) - 1

        # ── Doji ──
        if body(last) <= 0.1 * (c['high'][last] - c['low'][last]):
            patterns.append(("Doji", "⚪", "خنثی - بازگشت احتمالی"))

        # ── Hammer ──
        if (lower_shadow(last) >= 2 * body(last) and
                upper_shadow(last) <= 0.3 * body(last) and
                is_bull(last)):
            patterns.append(("Hammer", "🔨", "صعودی - برگشت از کف"))

        # ── Shooting Star ──
        if (upper_shadow(last) >= 2 * body(last) and
                lower_shadow(last) <= 0.3 * body(last) and
                is_bear(last)):
            patterns.append(("Shooting Star", "⭐", "نزولی - برگشت از سقف"))

        # ── Engulfing ──
        if last >= 1:
            if (is_bull(last) and is_bear(last - 1) and
                    c['close'][last] > c['open'][last - 1] and
                    c['open'][last] < c['close'][last - 1]):
                patterns.append(("Bullish Engulfing", "📈", "صعودی قوی"))
            elif (is_bear(last) and is_bull(last - 1) and
                  c['close'][last] < c['open'][last - 1] and
                  c['open'][last] > c['close'][last - 1]):
                patterns.append(("Bearish Engulfing", "📉", "نزولی قوی"))

        # ── Morning Star ──
        if last >= 2:
            if (is_bear(last - 2) and
                    body(last - 1) < 0.3 * body(last - 2) and
                    is_bull(last) and
                    c['close'][last] > (c['open'][last - 2] + c['close'][last - 2]) / 2):
                patterns.append(("Morning Star", "🌅", "صعودی - برگشت قوی از کف"))

        # ── Evening Star ──
        if last >= 2:
            if (is_bull(last - 2) and
                    body(last - 1) < 0.3 * body(last - 2) and
                    is_bear(last) and
                    c['close'][last] < (c['open'][last - 2] + c['close'][last - 2]) / 2):
                patterns.append(("Evening Star", "🌆", "نزولی - برگشت قوی از سقف"))

        # ── Marubozu Bull ──
        if (is_bull(last) and
                upper_shadow(last) < 0.05 * body(last) and
                lower_shadow(last) < 0.05 * body(last) and
                body(last) > 0.7 * (c['high'][last] - c['low'][last])):
            patterns.append(("Bullish Marubozu", "💚", "صعودی قوی - فشار خرید"))

        # ── Marubozu Bear ──
        if (is_bear(last) and
                upper_shadow(last) < 0.05 * body(last) and
                lower_shadow(last) < 0.05 * body(last) and
                body(last) > 0.7 * (c['high'][last] - c['low'][last])):
            patterns.append(("Bearish Marubozu", "❤️", "نزولی قوی - فشار فروش"))

        # ── Spinning Top ──
        if (body(last) < 0.3 * (c['high'][last] - c['low'][last]) and
                upper_shadow(last) > body(last) and
                lower_shadow(last) > body(last)):
            patterns.append(("Spinning Top", "🌀", "عدم قطعیت در بازار"))

        # ── Three White Soldiers ──
        if last >= 2:
            if all(is_bull(i) for i in [last, last - 1, last - 2]) and \
               c['close'][last] > c['close'][last - 1] > c['close'][last - 2] and \
               c['open'][last] < c['close'][last - 1] and \
               c['open'][last - 1] < c['close'][last - 2]:
                patterns.append(("Three White Soldiers", "🪖", "صعودی قوی - روند صعودی"))

        # ── Three Black Crows ──
        if last >= 2:
            if all(is_bear(i) for i in [last, last - 1, last - 2]) and \
               c['close'][last] < c['close'][last - 1] < c['close'][last - 2]:
                patterns.append(("Three Black Crows", "🐦‍⬛", "نزولی قوی - روند نزولی"))

        return patterns

    # ─────────────────────────────────────────────
    # TREND ANALYSIS
    # ─────────────────────────────────────────────

    def determine_trend(self, df: pd.DataFrame) -> tuple:
        close = df['close']
        ema20 = self.calc_ema(close, 20).iloc[-1]
        ema50 = self.calc_ema(close, 50).iloc[-1]
        ema200 = self.calc_ema(close, 200).iloc[-1]
        price = close.iloc[-1]

        bullish_count = sum([price > ema20, price > ema50, price > ema200, ema20 > ema50, ema50 > ema200])

        if bullish_count >= 4:
            return "صعودی قوی 📈", "bullish"
        elif bullish_count == 3:
            return "صعودی ضعیف 📈", "mild_bullish"
        elif bullish_count == 2:
            return "خنثی ↔️", "neutral"
        elif bullish_count == 1:
            return "نزولی ضعیف 📉", "mild_bearish"
        else:
            return "نزولی قوی 📉", "bearish"

    # ─────────────────────────────────────────────
    # SUPPORT / RESISTANCE
    # ─────────────────────────────────────────────

    def find_support_resistance(self, df: pd.DataFrame, window: int = 10) -> tuple:
        highs = df['high'].values
        lows = df['low'].values
        resistances, supports = [], []

        for i in range(window, len(df) - window):
            if highs[i] == max(highs[i - window:i + window]):
                resistances.append(highs[i])
            if lows[i] == min(lows[i - window:i + window]):
                supports.append(lows[i])

        price = df['close'].iloc[-1]
        resistances = sorted([r for r in resistances if r > price], reverse=False)[:3]
        supports = sorted([s for s in supports if s < price], reverse=True)[:3]
        return supports, resistances

    # ─────────────────────────────────────────────
    # SIGNAL SCORING
    # ─────────────────────────────────────────────

    def compute_signal(self, df: pd.DataFrame, patterns: list, trend_type: str) -> dict:
        close = df['close']
        price = close.iloc[-1]

        rsi = self.calc_rsi(close).iloc[-1]
        macd, signal, hist = self.calc_macd(close)
        macd_val = macd.iloc[-1]
        signal_val = signal.iloc[-1]
        hist_val = hist.iloc[-1]
        bb_upper, bb_mid, bb_lower = self.calc_bollinger(close)

        long_score = 0
        short_score = 0

        # RSI
        if rsi < 30:
            long_score += 3
        elif rsi < 45:
            long_score += 1
        elif rsi > 70:
            short_score += 3
        elif rsi > 55:
            short_score += 1

        # MACD
        if macd_val > signal_val and hist_val > 0:
            long_score += 2
        elif macd_val < signal_val and hist_val < 0:
            short_score += 2

        # Bollinger
        bb_u = bb_upper.iloc[-1]
        bb_l = bb_lower.iloc[-1]
        if price < bb_l:
            long_score += 2
        elif price > bb_u:
            short_score += 2

        # Trend
        trend_map = {
            "bullish": (3, 0), "mild_bullish": (1, 0),
            "neutral": (0, 0), "mild_bearish": (0, 1), "bearish": (0, 3)
        }
        ls, ss = trend_map.get(trend_type, (0, 0))
        long_score += ls
        short_score += ss

        # Patterns
        bull_patterns = ["Hammer", "Bullish Engulfing", "Morning Star", "Bullish Marubozu", "Three White Soldiers"]
        bear_patterns = ["Shooting Star", "Bearish Engulfing", "Evening Star", "Bearish Marubozu", "Three Black Crows"]
        for name, _, _ in patterns:
            if name in bull_patterns:
                long_score += 2
            elif name in bear_patterns:
                short_score += 2

        return {
            "long_score": long_score,
            "short_score": short_score,
            "rsi": rsi,
            "macd": macd_val,
            "signal": signal_val,
            "histogram": hist_val,
            "bb_upper": bb_u,
            "bb_lower": bb_l,
            "bb_mid": bb_mid.iloc[-1],
        }

    # ─────────────────────────────────────────────
    # MAIN ANALYSIS
    # ─────────────────────────────────────────────

    def analyze(self, symbol: str, timeframe: str) -> str:
        df = self.fetch_ohlcv(symbol, timeframe, limit=200)
        price = df['close'].iloc[-1]
        high_24h = df['high'].tail(24).max()
        low_24h = df['low'].tail(24).min()
        volume = df['volume'].tail(24).sum()

        patterns = self.detect_patterns(df)
        trend_label, trend_type = self.determine_trend(df)
        fib_levels, swing_high, swing_low = self.calc_fibonacci(df)
        nearest_fibs = self.nearest_fib_levels(price, fib_levels)
        supports, resistances = self.find_support_resistance(df)
        scores = self.compute_signal(df, patterns, trend_type)

        long_score = scores['long_score']
        short_score = scores['short_score']
        total = long_score + short_score

        def pct(s): return round((s / total * 100) if total > 0 else 50)

        long_pct = pct(long_score)
        short_pct = pct(short_score)

        # Determine primary signal
        if long_score > short_score + 3:
            primary = "🟢 LONG قوی"
            emoji = "🚀"
        elif long_score > short_score:
            primary = "🟡 LONG ضعیف"
            emoji = "📈"
        elif short_score > long_score + 3:
            primary = "🔴 SHORT قوی"
            emoji = "📉"
        elif short_score > long_score:
            primary = "🟡 SHORT ضعیف"
            emoji = "⬇️"
        else:
            primary = "⚪ خنثی"
            emoji = "↔️"

        # Entry / TP / SL calculation
        atr = (df['high'] - df['low']).tail(14).mean()

        if long_score >= short_score:
            entry = price
            tp1 = round(price + 1.5 * atr, 4)
            tp2 = round(price + 2.5 * atr, 4)
            tp3 = round(price + 4.0 * atr, 4)
            sl = round(price - 1.0 * atr, 4)
            rr = round((tp2 - entry) / (entry - sl), 2) if entry != sl else "N/A"
        else:
            entry = price
            tp1 = round(price - 1.5 * atr, 4)
            tp2 = round(price - 2.5 * atr, 4)
            tp3 = round(price - 4.0 * atr, 4)
            sl = round(price + 1.0 * atr, 4)
            rr = round((entry - tp2) / (sl - entry), 2) if entry != sl else "N/A"

        # ── Build message ──
        tf_names = {"1m": "1 دقیقه", "5m": "5 دقیقه", "15m": "15 دقیقه",
                    "1h": "1 ساعت", "4h": "4 ساعت", "1d": "روزانه", "1w": "هفتگی"}

        lines = [
            f"{'═' * 28}",
            f"  {emoji} تحلیل {symbol}USDT  {emoji}",
            f"  تایم‌فریم: {tf_names.get(timeframe, timeframe)}",
            f"{'═' * 28}",
            f"",
            f"💰 قیمت فعلی: `{price:,.4f}` USDT",
            f"📊 روند کلی: {trend_label}",
            f"",
            f"{'─' * 28}",
            f"📡 سیگنال اصلی: *{primary}*",
            f"",
            f"  📈 احتمال LONG:  {long_pct}%",
            f"  📉 احتمال SHORT: {short_pct}%",
            f"{'─' * 28}",
        ]

        # Entry / TP / SL
        direction = "LONG" if long_score >= short_score else "SHORT"
        lines += [
            f"",
            f"🎯 *پیشنهاد معامله {direction}:*",
            f"  ✅ ورود:     `{entry:,.4f}`",
            f"  🎯 TP1:     `{tp1:,.4f}`",
            f"  🎯 TP2:     `{tp2:,.4f}`",
            f"  🎯 TP3:     `{tp3:,.4f}`",
            f"  🛑 SL:      `{sl:,.4f}`",
            f"  ⚖️  R/R:     {rr}",
            f"",
        ]

        # Indicators
        rsi_emoji = "🔴" if scores['rsi'] > 70 else "🟢" if scores['rsi'] < 30 else "🟡"
        macd_emoji = "🟢" if scores['histogram'] > 0 else "🔴"

        lines += [
            f"{'─' * 28}",
            f"📊 *اندیکاتورها:*",
            f"  {rsi_emoji} RSI(14):    `{scores['rsi']:.1f}`",
            f"  {macd_emoji} MACD:       `{scores['macd']:.4f}`",
            f"  📶 Signal:    `{scores['signal']:.4f}`",
            f"  📊 Histogram: `{scores['histogram']:.4f}`",
            f"  🔼 BB Upper:  `{scores['bb_upper']:,.4f}`",
            f"  ➖ BB Mid:    `{scores['bb_mid']:,.4f}`",
            f"  🔽 BB Lower:  `{scores['bb_lower']:,.4f}`",
            f"",
        ]

        # Fibonacci
        lines += [
            f"{'─' * 28}",
            f"🌀 *سطوح فیبوناچی (نزدیک‌ترین):*",
            f"  📍 سوئینگ High: `{swing_high:,.4f}`",
            f"  📍 سوئینگ Low:  `{swing_low:,.4f}`",
        ]
        for lvl_name, lvl_price in nearest_fibs:
            dist_pct = round((lvl_price - price) / price * 100, 2)
            arrow = "⬆️" if lvl_price > price else "⬇️"
            lines.append(f"  {arrow} {lvl_name}: `{lvl_price:,.4f}` ({dist_pct:+.2f}%)")

        lines.append("")

        # Support / Resistance
        lines += [f"{'─' * 28}", f"🧱 *حمایت و مقاومت:*"]
        if resistances:
            lines.append("  🔴 مقاومت‌ها:")
            for r in resistances:
                lines.append(f"    • `{r:,.4f}`")
        if supports:
            lines.append("  🟢 حمایت‌ها:")
            for s in supports:
                lines.append(f"    • `{s:,.4f}`")

        lines.append("")

        # Candlestick patterns
        lines += [f"{'─' * 28}", f"🕯 *الگوهای کندل‌استیک:*"]
        if patterns:
            for name, pat_emoji, desc in patterns:
                lines.append(f"  {pat_emoji} {name}: {desc}")
        else:
            lines.append("  ⚪ الگوی خاصی شناسایی نشد")

        lines += [
            f"",
            f"{'─' * 28}",
            f"⚠️ *هشدار:* این تحلیل صرفاً بر پایه داده‌های تکنیکال",
            f"است و توصیه مالی نمی‌باشد. مدیریت ریسک فراموش نشود.",
            f"{'═' * 28}",
            f"🕐 {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC",
        ]

        return "\n".join(lines)
