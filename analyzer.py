import os
import ccxt
import requests
import pandas as pd
import numpy as np
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

LABELS = {
    'fa': {
        'tf_names': {"1m": "1 دقیقه", "5m": "5 دقیقه", "15m": "15 دقیقه", "1h": "1 ساعت", "4h": "4 ساعت", "1d": "روزانه", "1w": "هفتگی"},
        'trend': {'bullish': "صعودی قوی 📈", 'mild_bullish': "صعودی ضعیف 📈", 'neutral': "خنثی ↔️",
                  'mild_bearish': "نزولی ضعیف 📉", 'bearish': "نزولی قوی 📉"},
        'vol_trend': {'up': 'افزایشی', 'down': 'کاهشی', 'flat': 'ثابت'},
        'direction_word': {'bull': 'صعودی', 'bear': 'نزولی'},
        'pattern_desc': {
            'doji': 'خنثی', 'hammer': 'صعودی - برگشت از کف', 'shooting_star': 'نزولی - برگشت از سقف',
            'bullish_engulfing': 'صعودی قوی', 'bearish_engulfing': 'نزولی قوی',
            'morning_star': 'صعودی قوی از کف', 'evening_star': 'نزولی قوی از سقف',
            'bullish_marubozu': 'صعودی قوی', 'bearish_marubozu': 'نزولی قوی',
            'three_white_soldiers': 'صعودی قوی', 'three_black_crows': 'نزولی قوی',
        },
        'signal_primary': {'long_strong': "🟢 LONG قوی", 'long_weak': "🟡 LONG ضعیف",
                           'short_strong': "🔴 SHORT قوی", 'short_weak': "🟡 SHORT ضعیف", 'neutral': "⚪ خنثی"},
        'strength': {'strong': 'قوی', 'medium': 'متوسط'},
        'next_level': {'support': 'حمایت بعدی', 'resistance': 'مقاومت بعدی'},
        'ui': {
            'analysis_title': 'تحلیل', 'timeframe': 'تایم‌فریم', 'price': 'قیمت', 'trend': 'روند',
            'data_source': '📡 منبع دیتا',
            'signal': 'سیگنال', 'suggestion': 'پیشنهاد', 'entry': 'ورود', 'rr': 'R/R',
            'key_sr': 'حمایت و مقاومت کلیدی', 'resistances': 'مقاومت‌ها', 'supports': 'حمایت‌ها',
            'scenarios': 'سناریوهای قیمتی', 'bear_scenario': 'سناریو نزولی', 'bull_scenario': 'سناریو صعودی',
            'if_breaks': 'اگر `{price}` بشکند:', 'drop_estimate': 'تخمین ریزش', 'pump_estimate': 'تخمین رشد',
            'fibonacci': 'فیبوناچی (نزدیک‌ترین)', 'indicators': 'اندیکاتورها', 'volume_section': 'حجم معاملات',
            'patterns_section': 'الگوهای کندل', 'no_pattern': 'الگوی خاصی شناسایی نشد',
            'disclaimer': 'این تحلیل توصیه مالی نیست.',
            'last_candle_volume': 'حجم کندل آخر', 'avg_20_candle': 'میانگین ۲۰ کندل', 'of_avg': 'میانگین',
            'volume_trend_5': 'روند حجم (۵ کندل اخیر)', 'volume_spike': 'اسپایک حجمی — حرکت اخیر با قدرت بالایی همراه بوده',
            'volume_low': 'حجم پایین — این حرکت پشتوانه معاملاتی ضعیفی دارد',
            'volume_confirms': 'حجم، حرکت {direction} کندل آخر را تایید می‌کند',
            'volume_confirmed_tag': 'تایید حجمی',
        },
    },
    'en': {
        'tf_names': {"1m": "1 Min", "5m": "5 Min", "15m": "15 Min", "1h": "1 Hour", "4h": "4 Hour", "1d": "Daily", "1w": "Weekly"},
        'trend': {'bullish': "Strong Bullish 📈", 'mild_bullish': "Mild Bullish 📈", 'neutral': "Neutral ↔️",
                  'mild_bearish': "Mild Bearish 📉", 'bearish': "Strong Bearish 📉"},
        'vol_trend': {'up': 'Rising', 'down': 'Falling', 'flat': 'Flat'},
        'direction_word': {'bull': 'bullish', 'bear': 'bearish'},
        'pattern_desc': {
            'doji': 'Neutral', 'hammer': 'Bullish - reversal from the bottom', 'shooting_star': 'Bearish - reversal from the top',
            'bullish_engulfing': 'Strong bullish', 'bearish_engulfing': 'Strong bearish',
            'morning_star': 'Strong bullish reversal from the bottom', 'evening_star': 'Strong bearish reversal from the top',
            'bullish_marubozu': 'Strong bullish', 'bearish_marubozu': 'Strong bearish',
            'three_white_soldiers': 'Strong bullish', 'three_black_crows': 'Strong bearish',
        },
        'signal_primary': {'long_strong': "🟢 Strong LONG", 'long_weak': "🟡 Weak LONG",
                           'short_strong': "🔴 Strong SHORT", 'short_weak': "🟡 Weak SHORT", 'neutral': "⚪ Neutral"},
        'strength': {'strong': 'strong', 'medium': 'medium'},
        'next_level': {'support': 'Next support', 'resistance': 'Next resistance'},
        'ui': {
            'analysis_title': 'Analysis', 'timeframe': 'Timeframe', 'price': 'Price', 'trend': 'Trend',
            'data_source': '📡 Data source',
            'signal': 'Signal', 'suggestion': 'suggestion', 'entry': 'Entry', 'rr': 'R/R',
            'key_sr': 'Key Support & Resistance', 'resistances': 'Resistances', 'supports': 'Supports',
            'scenarios': 'Price Scenarios', 'bear_scenario': 'Bearish Scenario', 'bull_scenario': 'Bullish Scenario',
            'if_breaks': 'If `{price}` breaks:', 'drop_estimate': 'Estimated drop', 'pump_estimate': 'Estimated rise',
            'fibonacci': 'Fibonacci (Nearest)', 'indicators': 'Indicators', 'volume_section': 'Volume',
            'patterns_section': 'Candlestick Patterns', 'no_pattern': 'No specific pattern detected',
            'disclaimer': 'This analysis is not financial advice.',
            'last_candle_volume': 'Last candle volume', 'avg_20_candle': '20-candle average', 'of_avg': 'of average',
            'volume_trend_5': 'Volume trend (last 5 candles)', 'volume_spike': 'Volume spike — recent move backed by strong participation',
            'volume_low': 'Low volume — this move has weak trading support',
            'volume_confirms': 'Volume confirms the {direction} move of the last candle',
            'volume_confirmed_tag': 'volume-confirmed',
        },
    },
    'ru': {
        'tf_names': {"1m": "1 Мин", "5m": "5 Мин", "15m": "15 Мин", "1h": "1 Час", "4h": "4 Часа", "1d": "День", "1w": "Неделя"},
        'trend': {'bullish': "Сильный рост 📈", 'mild_bullish': "Слабый рост 📈", 'neutral': "Нейтрально ↔️",
                  'mild_bearish': "Слабое падение 📉", 'bearish': "Сильное падение 📉"},
        'vol_trend': {'up': 'Растёт', 'down': 'Падает', 'flat': 'Стабильно'},
        'direction_word': {'bull': 'бычье', 'bear': 'медвежье'},
        'pattern_desc': {
            'doji': 'Нейтрально', 'hammer': 'Бычий - разворот снизу', 'shooting_star': 'Медвежий - разворот сверху',
            'bullish_engulfing': 'Сильный бычий', 'bearish_engulfing': 'Сильный медвежий',
            'morning_star': 'Сильный бычий разворот снизу', 'evening_star': 'Сильный медвежий разворот сверху',
            'bullish_marubozu': 'Сильный бычий', 'bearish_marubozu': 'Сильный медвежий',
            'three_white_soldiers': 'Сильный бычий', 'three_black_crows': 'Сильный медвежий',
        },
        'signal_primary': {'long_strong': "🟢 Сильный LONG", 'long_weak': "🟡 Слабый LONG",
                           'short_strong': "🔴 Сильный SHORT", 'short_weak': "🟡 Слабый SHORT", 'neutral': "⚪ Нейтрально"},
        'strength': {'strong': 'сильный', 'medium': 'средний'},
        'next_level': {'support': 'Следующая поддержка', 'resistance': 'Следующее сопротивление'},
        'ui': {
            'analysis_title': 'Анализ', 'timeframe': 'Таймфрейм', 'price': 'Цена', 'trend': 'Тренд',
            'data_source': '📡 Источник данных',
            'signal': 'Сигнал', 'suggestion': 'рекомендация', 'entry': 'Вход', 'rr': 'R/R',
            'key_sr': 'Ключевые уровни', 'resistances': 'Сопротивления', 'supports': 'Поддержки',
            'scenarios': 'Ценовые сценарии', 'bear_scenario': 'Медвежий сценарий', 'bull_scenario': 'Бычий сценарий',
            'if_breaks': 'Если `{price}` будет пробит:', 'drop_estimate': 'Ожидаемое падение', 'pump_estimate': 'Ожидаемый рост',
            'fibonacci': 'Фибоначчи (ближайшие)', 'indicators': 'Индикаторы', 'volume_section': 'Объём',
            'patterns_section': 'Свечные модели', 'no_pattern': 'Особых моделей не обнаружено',
            'disclaimer': 'Этот анализ не является финансовым советом.',
            'last_candle_volume': 'Объём последней свечи', 'avg_20_candle': 'Средний за 20 свечей', 'of_avg': 'от среднего',
            'volume_trend_5': 'Тренд объёма (5 свечей)', 'volume_spike': 'Всплеск объёма — движение подкреплено высокой активностью',
            'volume_low': 'Низкий объём — движение слабо подкреплено торговлей',
            'volume_confirms': 'Объём подтверждает {direction} движение последней свечи',
            'volume_confirmed_tag': 'подтверждено объёмом',
        },
    },
}


class CryptoAnalyzer:
    COINGECKO_BASE = "https://api.coingecko.com/api/v3"
    CMC_BASE = "https://pro-api.coinmarketcap.com/v2"
    CMC_API_KEY = os.environ.get("CMC_API_KEY")  # only useful on CMC's paid Startup+ tier — see note below
    SOURCE_ORDER = ['kucoin', 'mexc', 'coingecko', 'coinmarketcap']
    SOURCE_NAMES = {'kucoin': 'KuCoin', 'mexc': 'MEXC', 'coingecko': 'CoinGecko', 'coinmarketcap': 'CoinMarketCap'}

    def __init__(self):
        self.exchange = ccxt.kucoin({'enableRateLimit': True, 'timeout': 15000})
        self.exchange_mexc = ccxt.mexc({'enableRateLimit': True, 'timeout': 15000})
        self._cg_id_cache = {}
        self.last_source = None  # 'kucoin' / 'mexc' / 'coingecko' / 'coinmarketcap' — set by the most recent fetch_ohlcv call
        self.last_source_note = None  # human-readable caveat about the active source, if any

    def _fetch_ohlcv_exchange(self, exchange, symbol, timeframe, limit):
        pair = f"{symbol}/USDT"
        ohlcv = exchange.fetch_ohlcv(pair, timeframe, limit=limit)
        if not ohlcv:
            raise ValueError("exchange returned no candles")
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df

    def fetch_ohlcv(self, symbol, timeframe, limit=300, preferred_source=None):
        """Tries sources in order: KuCoin, MEXC (real exchanges, exact
        candles + real volume), then CoinGecko and CoinMarketCap (approximate
        granularity, fallback only). If preferred_source is set, that source
        is tried first — but if it doesn't have the coin, the rest of the
        chain still runs, so a preference never turns into a hard failure."""
        order = list(self.SOURCE_ORDER)
        if preferred_source in order:
            order.remove(preferred_source)
            order.insert(0, preferred_source)

        tried = []
        for source in order:
            tried.append(self.SOURCE_NAMES[source])
            try:
                if source == 'kucoin':
                    df = self._fetch_ohlcv_exchange(self.exchange, symbol, timeframe, limit)
                    self.last_source, self.last_source_note = 'kucoin', None
                    return df

                elif source == 'mexc':
                    df = self._fetch_ohlcv_exchange(self.exchange_mexc, symbol, timeframe, limit)
                    self.last_source, self.last_source_note = 'mexc', None
                    return df

                elif source == 'coingecko':
                    df, note = self._fetch_ohlcv_coingecko(symbol, timeframe, limit)
                    self.last_source, self.last_source_note = 'coingecko', note
                    return df

                elif source == 'coinmarketcap':
                    if not self.CMC_API_KEY:
                        tried.pop()  # not actually attempted — no key configured
                        continue
                    df, note = self._fetch_ohlcv_cmc(symbol, timeframe, limit)
                    self.last_source, self.last_source_note = 'coinmarketcap', note
                    return df
            except Exception as e:
                logger.warning(f"{self.SOURCE_NAMES[source]} fetch failed for {symbol} ({e})")
                continue

        raise ValueError(f"{symbol} was not found on any source ({', '.join(tried)})")

    def _coingecko_lookup_id(self, symbol):
        symbol_u = symbol.upper()
        if symbol_u in self._cg_id_cache:
            return self._cg_id_cache[symbol_u]
        try:
            resp = requests.get(f"{self.COINGECKO_BASE}/search", params={"query": symbol_u}, timeout=8)
            resp.raise_for_status()
            for coin in resp.json().get('coins', []):
                if coin.get('symbol', '').upper() == symbol_u:
                    self._cg_id_cache[symbol_u] = coin['id']
                    return coin['id']
        except Exception as e:
            logger.error(f"CoinGecko id lookup failed for {symbol}: {e}")
        return None

    def _fetch_ohlcv_coingecko(self, symbol, timeframe, limit=300):
        """CoinGecko's free /ohlc endpoint has two hard limits we can't work
        around on the free tier: no per-candle volume, and fixed granularity
        tied to the 'days' window (not a free choice of timeframe). We pick
        the closest available granularity and mark volume as unavailable
        rather than showing fabricated numbers."""
        coin_id = self._coingecko_lookup_id(symbol)
        if not coin_id:
            raise ValueError(f"{symbol} not found on KuCoin or CoinGecko")

        days_map = {"1m": 1, "5m": 1, "15m": 1, "1h": 7, "4h": 30, "1d": 90, "1w": 365}
        granularity_map = {"1m": "~30m", "5m": "~30m", "15m": "~30m", "1h": "~4h",
                            "4h": "~4h", "1d": "~4d", "1w": "~4d"}
        days = days_map.get(timeframe, 30)

        resp = requests.get(f"{self.COINGECKO_BASE}/coins/{coin_id}/ohlc",
                             params={"vs_currency": "usd", "days": days}, timeout=8)
        resp.raise_for_status()
        raw = resp.json()
        if not raw:
            raise ValueError(f"CoinGecko has no OHLC data for {symbol}")

        df = pd.DataFrame(raw, columns=['timestamp', 'open', 'high', 'low', 'close'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['volume'] = 0.0  # not available on CoinGecko's free OHLC endpoint
        df = df.tail(limit).reset_index(drop=True)
        note = f"CoinGecko ({granularity_map.get(timeframe, '?')} candles, volume unavailable — {symbol} isn't on KuCoin or MEXC)"
        return df, note

    def _fetch_ohlcv_cmc(self, symbol, timeframe, limit=300):
        """CoinMarketCap's free 'Basic' tier does NOT include historical
        OHLCV at all — /cryptocurrency/ohlcv/historical requires their paid
        Startup tier or above. This only does anything if CMC_API_KEY is set
        to a key from a paid plan; otherwise fetch_ohlcv skips this source
        entirely."""
        period_map = {"1m": "hourly", "5m": "hourly", "15m": "hourly", "1h": "hourly",
                      "4h": "hourly", "1d": "daily", "1w": "daily"}
        time_period = period_map.get(timeframe, "daily")
        headers = {"X-CMC_PRO_API_KEY": self.CMC_API_KEY, "Accept": "application/json"}
        params = {"symbol": symbol.upper(), "time_period": time_period,
                  "count": min(limit, 300), "convert": "USD"}
        resp = requests.get(f"{self.CMC_BASE}/cryptocurrency/ohlcv/historical",
                             headers=headers, params=params, timeout=8)
        resp.raise_for_status()
        quotes = (resp.json().get('data') or {}).get('quotes', [])
        if not quotes:
            raise ValueError(f"CoinMarketCap has no OHLCV data for {symbol}")

        rows = []
        for q in quotes:
            usd = q.get('quote', {}).get('USD', {})
            rows.append({
                'timestamp': pd.to_datetime(q.get('time_close') or q.get('time_open')),
                'open': usd.get('open'), 'high': usd.get('high'),
                'low': usd.get('low'), 'close': usd.get('close'),
                'volume': usd.get('volume', 0),
            })
        df = pd.DataFrame(rows).sort_values('timestamp').tail(limit).reset_index(drop=True)
        note = f"CoinMarketCap ({time_period} candles, approximate for {timeframe} — {symbol} isn't on KuCoin, MEXC, or CoinGecko)"
        return df, note

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

    # ── Volume Analysis ──
    def calc_volume_analysis(self, df, period=20):
        volume = df['volume']
        close, open_ = df['close'], df['open']

        avg_volume = volume.rolling(period).mean().iloc[-1]
        current_volume = volume.iloc[-1]
        vol_ratio = current_volume / avg_volume if avg_volume and avg_volume > 0 else 1

        # Short-term trend: last 5 candles vs the 5 before them
        recent_avg = volume.tail(5).mean()
        prior_avg = volume.tail(10).head(5).mean()
        vol_trend_pct = round((recent_avg - prior_avg) / prior_avg * 100, 1) if prior_avg > 0 else 0
        if vol_trend_pct > 15: vol_trend = "up"
        elif vol_trend_pct < -15: vol_trend = "down"
        else: vol_trend = "flat"

        last_bullish = close.iloc[-1] > open_.iloc[-1]
        is_spike = vol_ratio >= 2.0
        is_high = vol_ratio >= 1.3
        is_low = vol_ratio <= 0.5
        # "Confirmation" = the latest candle's move is backed by meaningfully
        # above-average participation, which is what gives a breakout/pattern
        # credibility. Low-volume moves are flagged as weak/unreliable.
        confirms_move = is_high

        return {
            'avg_volume': avg_volume,
            'current_volume': current_volume,
            'vol_ratio': round(vol_ratio, 2),
            'vol_trend': vol_trend,
            'vol_trend_pct': vol_trend_pct,
            'is_spike': is_spike,
            'is_high': is_high,
            'is_low': is_low,
            'last_bullish': last_bullish,
            'confirms_move': confirms_move,
        }

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
    def calc_price_targets(self, df, supports, resistances, trend_type, fib_levels, lang='fa'):
        next_lvl = LABELS.get(lang, LABELS['fa'])['next_level']
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
                scenario_bear['targets'].append({'price': next_supports[0], 'label': next_lvl['support']})
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
                scenario_bull['targets'].append({'price': next_resistances[0], 'label': next_lvl['resistance']})
            if fib_above:
                scenario_bull['targets'].append({'price': round(fib_above[0][1], 6), 'label': f'Fib {fib_above[0][0]}'})
            if next_resistances:
                pump_pct = round((next_resistances[0] - r1) / r1 * 100, 2)
                scenario_bull['pump_estimate'] = pump_pct
            targets['scenarios'].append(('bull', scenario_bull))

        return targets

    # ── Candlestick Patterns ──
    def detect_patterns(self, df, lang='fa'):
        pd_labels = LABELS.get(lang, LABELS['fa'])['pattern_desc']
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
            patterns.append(("Doji", "⚪", pd_labels['doji']))
        if lower_shadow(last) >= 2*body(last) and upper_shadow(last) <= 0.3*body(last) and is_bull(last):
            patterns.append(("Hammer", "🔨", pd_labels['hammer']))
        if upper_shadow(last) >= 2*body(last) and lower_shadow(last) <= 0.3*body(last) and is_bear(last):
            patterns.append(("Shooting Star", "⭐", pd_labels['shooting_star']))
        if last >= 1:
            if is_bull(last) and is_bear(last-1) and c['close'][last] > c['open'][last-1] and c['open'][last] < c['close'][last-1]:
                patterns.append(("Bullish Engulfing", "📈", pd_labels['bullish_engulfing']))
            elif is_bear(last) and is_bull(last-1) and c['close'][last] < c['open'][last-1] and c['open'][last] > c['close'][last-1]:
                patterns.append(("Bearish Engulfing", "📉", pd_labels['bearish_engulfing']))
        if last >= 2:
            if is_bear(last-2) and body(last-1) < 0.3*body(last-2) and is_bull(last) and c['close'][last] > (c['open'][last-2]+c['close'][last-2])/2:
                patterns.append(("Morning Star", "🌅", pd_labels['morning_star']))
            if is_bull(last-2) and body(last-1) < 0.3*body(last-2) and is_bear(last) and c['close'][last] < (c['open'][last-2]+c['close'][last-2])/2:
                patterns.append(("Evening Star", "🌆", pd_labels['evening_star']))
        if is_bull(last) and upper_shadow(last) < 0.05*body(last) and lower_shadow(last) < 0.05*body(last) and body(last) > 0.7*(c['high'][last]-c['low'][last]):
            patterns.append(("Bullish Marubozu", "💚", pd_labels['bullish_marubozu']))
        if is_bear(last) and upper_shadow(last) < 0.05*body(last) and lower_shadow(last) < 0.05*body(last) and body(last) > 0.7*(c['high'][last]-c['low'][last]):
            patterns.append(("Bearish Marubozu", "❤️", pd_labels['bearish_marubozu']))
        if last >= 2:
            if all(is_bull(i) for i in [last, last-1, last-2]) and c['close'][last] > c['close'][last-1] > c['close'][last-2]:
                patterns.append(("Three White Soldiers", "🪖", pd_labels['three_white_soldiers']))
            if all(is_bear(i) for i in [last, last-1, last-2]) and c['close'][last] < c['close'][last-1] < c['close'][last-2]:
                patterns.append(("Three Black Crows", "🐦‍⬛", pd_labels['three_black_crows']))

        return patterns

    # ── Trend ──
    def determine_trend(self, df, lang='fa'):
        trend_labels = LABELS.get(lang, LABELS['fa'])['trend']
        close = df['close']
        ema20 = self.calc_ema(close, 20).iloc[-1]
        ema50 = self.calc_ema(close, 50).iloc[-1]
        ema200 = self.calc_ema(close, 200).iloc[-1]
        price = close.iloc[-1]
        count = sum([price > ema20, price > ema50, price > ema200, ema20 > ema50, ema50 > ema200])
        if count >= 4: return trend_labels['bullish'], "bullish"
        elif count == 3: return trend_labels['mild_bullish'], "mild_bullish"
        elif count == 2: return trend_labels['neutral'], "neutral"
        elif count == 1: return trend_labels['mild_bearish'], "mild_bearish"
        else: return trend_labels['bearish'], "bearish"

    # ── Signal Score ──
    def compute_signal(self, df, patterns, trend_type):
        close = df['close']
        price = close.iloc[-1]
        rsi = self.calc_rsi(close).iloc[-1]
        macd, signal, hist = self.calc_macd(close)
        bb_upper, bb_mid, bb_lower = self.calc_bollinger(close)
        vol = self.calc_volume_analysis(df)

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

        # Volume: an above-average-volume candle adds conviction to whichever
        # direction it closed; a spike adds even more. Low-volume candles add
        # nothing, since a move with weak participation is less trustworthy.
        if vol['is_high']:
            vol_points = 2 if vol['is_spike'] else 1
            if vol['last_bullish']: long_score += vol_points
            else: short_score += vol_points

        return {
            'long_score': long_score, 'short_score': short_score,
            'rsi': rsi, 'macd': macd.iloc[-1], 'signal': signal.iloc[-1],
            'histogram': hist.iloc[-1], 'bb_upper': bb_upper.iloc[-1],
            'bb_lower': bb_lower.iloc[-1], 'bb_mid': bb_mid.iloc[-1],
            'volume': vol,
        }

    # ── MAIN ANALYZE ──
    def analyze(self, symbol, timeframe, lang='fa', preferred_source=None):
        L = LABELS.get(lang, LABELS['fa'])
        ui = L['ui']
        df = self.fetch_ohlcv(symbol, timeframe, limit=300, preferred_source=preferred_source)
        source_display = self.SOURCE_NAMES.get(self.last_source, self.last_source or 'KuCoin')
        price = df['close'].iloc[-1]

        patterns = self.detect_patterns(df, lang)
        trend_label, trend_type = self.determine_trend(df, lang)
        fib_levels, swing_high, swing_low = self.calc_fibonacci(df)
        supports, resistances = self.find_support_resistance(df)
        key_supports, key_resistances = self.find_key_levels(df)
        scores = self.compute_signal(df, patterns, trend_type)
        targets = self.calc_price_targets(df, supports, resistances, trend_type, fib_levels, lang)
        atr = self.calc_atr(df).iloc[-1]

        long_score = scores['long_score']
        short_score = scores['short_score']
        total = long_score + short_score
        long_pct = round(long_score/total*100) if total > 0 else 50
        short_pct = 100 - long_pct

        sp = L['signal_primary']
        if long_score > short_score + 3: primary, emoji = sp['long_strong'], "🚀"
        elif long_score > short_score: primary, emoji = sp['long_weak'], "📈"
        elif short_score > long_score + 3: primary, emoji = sp['short_strong'], "📉"
        elif short_score > long_score: primary, emoji = sp['short_weak'], "⬇️"
        else: primary, emoji = sp['neutral'], "↔️"

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

        lines = [
            f"{'═'*28}",
            f"  {emoji} {ui['analysis_title']} {symbol}USDT  {emoji}",
            f"  {ui['timeframe']}: {L['tf_names'].get(timeframe, timeframe)}",
            f"{'═'*28}",
            f"",
            f"💰 {ui['price']}: `{price:,.6f}` USDT",
            f"📊 {ui['trend']}: {trend_label}",
            f"{ui['data_source']}: {source_display}",
            f"",
            f"📡 {ui['signal']}: *{primary}*",
            f"  📈 LONG: {long_pct}%  |  📉 SHORT: {short_pct}%",
            f"",
            f"🎯 *{direction} {ui['suggestion']}:*",
            f"  ✅ {ui['entry']}:  `{entry:,.6f}`",
            f"  🎯 TP1:  `{tp1:,.6f}`",
            f"  🎯 TP2:  `{tp2:,.6f}`",
            f"  🎯 TP3:  `{tp3:,.6f}`",
            f"  🛑 SL:   `{sl:,.6f}`",
            f"  ⚖️  {ui['rr']}:  {rr}",
            f"",
        ]

        # ── Support / Resistance with Scenarios ──
        lines += [f"{'─'*28}", f"🧱 *{ui['key_sr']}:*", f""]

        if resistances:
            lines.append(f"  🔴 *{ui['resistances']}:*")
            for i, r in enumerate(resistances[:3]):
                dist = round((r - price) / price * 100, 2)
                strength = L['strength']['strong'] if i == 0 else L['strength']['medium']
                lines.append(f"    R{i+1}: `{r:,.6f}` (+{dist}%) — {strength}")

        if supports:
            lines.append("")
            lines.append(f"  🟢 *{ui['supports']}:*")
            for i, s in enumerate(supports[:3]):
                dist = round((price - s) / price * 100, 2)
                strength = L['strength']['strong'] if i == 0 else L['strength']['medium']
                lines.append(f"    S{i+1}: `{s:,.6f}` (-{dist}%) — {strength}")

        # ── Breakout Scenarios ──
        lines += [f"", f"{'─'*28}", f"🔮 *{ui['scenarios']}:*", f""]

        for stype, scenario in targets['scenarios']:
            trigger_str = f"{scenario['trigger']:,.6f}"
            if stype == 'bear':
                lines.append(f"  📉 *{ui['bear_scenario']}:*")
                lines.append(f"  {ui['if_breaks'].format(price=trigger_str)}")
                for tgt in scenario['targets']:
                    lines.append(f"    ↘️ {tgt['label']}: `{tgt['price']:,.6f}`")
                if 'drop_estimate' in scenario:
                    lines.append(f"    📏 {ui['drop_estimate']}: ~{scenario['drop_estimate']}%")
            else:
                lines.append(f"")
                lines.append(f"  📈 *{ui['bull_scenario']}:*")
                lines.append(f"  {ui['if_breaks'].format(price=trigger_str)}")
                for tgt in scenario['targets']:
                    lines.append(f"    ↗️ {tgt['label']}: `{tgt['price']:,.6f}`")
                if 'pump_estimate' in scenario:
                    lines.append(f"    📏 {ui['pump_estimate']}: ~{scenario['pump_estimate']}%")

        # ── Fibonacci ──
        nearest_fibs = sorted(fib_levels.items(), key=lambda x: abs(x[1]-price))[:4]
        lines += [f"", f"{'─'*28}", f"🌀 *{ui['fibonacci']}:*"]
        lines.append(f"  📍 High: `{swing_high:,.6f}` | Low: `{swing_low:,.6f}`")
        for lvl_name, lvl_price in nearest_fibs:
            dist = round((lvl_price - price) / price * 100, 2)
            arrow = "⬆️" if lvl_price > price else "⬇️"
            lines.append(f"  {arrow} {lvl_name}: `{lvl_price:,.6f}` ({dist:+.2f}%)")

        # ── Indicators ──
        rsi_emoji = "🔴" if scores['rsi'] > 70 else "🟢" if scores['rsi'] < 30 else "🟡"
        macd_emoji = "🟢" if scores['histogram'] > 0 else "🔴"
        lines += [
            f"", f"{'─'*28}", f"📊 *{ui['indicators']}:*",
            f"  {rsi_emoji} RSI(14): `{scores['rsi']:.1f}`",
            f"  {macd_emoji} MACD: `{scores['macd']:.6f}`",
            f"  📶 Histogram: `{scores['histogram']:.6f}`",
            f"  🔼 BB Upper: `{scores['bb_upper']:,.6f}`",
            f"  🔽 BB Lower: `{scores['bb_lower']:,.6f}`",
            f"  📏 ATR(14): `{atr:,.6f}`",
        ]

        # ── Volume ──
        vol = scores['volume']
        vol_trend_text = L['vol_trend'].get(vol['vol_trend'], vol['vol_trend'])
        vol_emoji = "🔥" if vol['is_spike'] else "🟢" if vol['is_high'] else "🔴" if vol['is_low'] else "🟡"
        trend_emoji = "📈" if vol['vol_trend'] == "up" else "📉" if vol['vol_trend'] == "down" else "➡️"
        lines += [f"", f"{'─'*28}", f"📶 *{ui['volume_section']}:*"]
        lines.append(f"  {vol_emoji} {ui['last_candle_volume']}: `{vol['current_volume']:,.2f}` ({vol['vol_ratio']}x {ui['of_avg']})")
        lines.append(f"  📊 {ui['avg_20_candle']}: `{vol['avg_volume']:,.2f}`")
        lines.append(f"  {trend_emoji} {ui['volume_trend_5']}: {vol_trend_text} ({vol['vol_trend_pct']:+.1f}%)")
        if vol['is_spike']:
            lines.append(f"  🔥 {ui['volume_spike']}")
        elif vol['is_low']:
            lines.append(f"  ⚠️ {ui['volume_low']}")
        if vol['confirms_move']:
            direction_txt = L['direction_word']['bull'] if vol['last_bullish'] else L['direction_word']['bear']
            lines.append(f"  ✅ {ui['volume_confirms'].format(direction=direction_txt)}")

        # ── Candlestick Patterns ──
        lines += [f"", f"{'─'*28}", f"🕯 *{ui['patterns_section']}:*"]
        bull_p = ["Hammer","Bullish Engulfing","Morning Star","Bullish Marubozu","Three White Soldiers"]
        bear_p = ["Shooting Star","Bearish Engulfing","Evening Star","Bearish Marubozu","Three Black Crows"]
        if patterns:
            for name, pat_emoji, desc in patterns:
                confirm_tag = ""
                if vol['is_high'] and ((name in bull_p and vol['last_bullish']) or (name in bear_p and not vol['last_bullish'])):
                    confirm_tag = f"  ✅ {ui['volume_confirmed_tag']}"
                lines.append(f"  {pat_emoji} {name}: {desc}{confirm_tag}")
        else:
            lines.append(f"  ⚪ {ui['no_pattern']}")

        lines += [
            f"", f"{'─'*28}",
            f"⚠️ {ui['disclaimer']}",
            f"{'═'*28}",
            f"🕐 {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC",
        ]

        return "\n".join(lines)


