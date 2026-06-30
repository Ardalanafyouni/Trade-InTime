import requests
import logging
from datetime import datetime, timedelta
from analyzer import CryptoAnalyzer

logger = logging.getLogger(__name__)

COINGECKO_BASE = "https://api.coingecko.com/api/v3"

analyzer = CryptoAnalyzer()


def fetch_coingecko(endpoint, params=None):
    try:
        r = requests.get(f"{COINGECKO_BASE}{endpoint}", params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.error(f"CoinGecko error: {e}")
        return None


def get_trending_coins():
    """Get trending coins from CoinGecko"""
    data = fetch_coingecko("/search/trending")
    if not data:
        return []
    coins = []
    for item in data.get('coins', [])[:7]:
        coin = item.get('item', {})
        coins.append({
            'id': coin.get('id'),
            'symbol': coin.get('symbol', '').upper(),
            'name': coin.get('name'),
            'market_cap_rank': coin.get('market_cap_rank'),
        })
    return coins


def get_top_gainers_losers():
    """Get top performers by weekly change"""
    data = fetch_coingecko("/coins/markets", params={
        'vs_currency': 'usd',
        'order': 'market_cap_desc',
        'per_page': 100,
        'page': 1,
        'price_change_percentage': '7d',
        'sparkline': False,
    })
    if not data:
        return [], []

    valid = [c for c in data if c.get('price_change_percentage_7d_in_currency') is not None]
    sorted_by_change = sorted(valid, key=lambda x: x.get('price_change_percentage_7d_in_currency', 0), reverse=True)

    gainers = sorted_by_change[:5]
    losers = sorted_by_change[-3:][::-1]
    return gainers, losers


def get_high_volume_coins():
    """Get coins with unusual volume spike"""
    data = fetch_coingecko("/coins/markets", params={
        'vs_currency': 'usd',
        'order': 'volume_desc',
        'per_page': 20,
        'page': 1,
        'sparkline': False,
    })
    if not data:
        return []
    return data[:5]


def get_coin_details(coin_id):
    """Get detailed info for a coin"""
    data = fetch_coingecko(f"/coins/{coin_id}", params={
        'localization': False,
        'tickers': False,
        'market_data': True,
        'community_data': False,
        'developer_data': False,
    })
    if not data:
        return None
    md = data.get('market_data', {})
    return {
        'name': data.get('name'),
        'symbol': data.get('symbol', '').upper(),
        'price': md.get('current_price', {}).get('usd'),
        'market_cap': md.get('market_cap', {}).get('usd'),
        'volume_24h': md.get('total_volume', {}).get('usd'),
        'change_24h': md.get('price_change_percentage_24h'),
        'change_7d': md.get('price_change_percentage_7d'),
        'ath': md.get('ath', {}).get('usd'),
        'ath_change': md.get('ath_change_percentage', {}).get('usd'),
        'description': data.get('description', {}).get('en', '')[:200],
    }


def get_technical_score(symbol):
    """Get technical score from our analyzer"""
    try:
        df = analyzer.fetch_ohlcv(symbol, '1d', limit=100)
        patterns = analyzer.detect_patterns(df)
        trend_label, trend_type = analyzer.determine_trend(df)
        scores = analyzer.compute_signal(df, patterns, trend_type)
        long_score = scores['long_score']
        short_score = scores['short_score']
        total = long_score + short_score
        long_pct = round(long_score / total * 100) if total > 0 else 50
        rsi = scores['rsi']
        return {
            'trend': trend_label,
            'trend_type': trend_type,
            'long_pct': long_pct,
            'rsi': round(rsi, 1),
            'signal': 'LONG' if long_score > short_score else 'SHORT' if short_score > long_score else 'NEUTRAL',
        }
    except:
        return None


def generate_watchlist():
    """Generate weekly watchlist combining CoinGecko + Technical Analysis"""

    now = datetime.utcnow()
    lines = [
        f"{'═'*30}",
        f"  📋 واچلیست هفتگی",
        f"  {now.strftime('%Y-%m-%d')} — هفته {now.isocalendar()[1]}",
        f"{'═'*30}",
        f"",
    ]

    # ── Trending coins ──
    trending = get_trending_coins()
    gainers, losers = get_top_gainers_losers()

    # Build watchlist: mix trending + top gainers
    watchlist_coins = []
    seen_symbols = set()

    # Add top gainers first
    for coin in gainers[:4]:
        sym = coin.get('symbol', '').upper()
        if sym and sym not in seen_symbols and sym not in ['USDT', 'USDC', 'BUSD', 'DAI']:
            watchlist_coins.append({
                'symbol': sym,
                'name': coin.get('name'),
                'change_7d': round(coin.get('price_change_percentage_7d_in_currency', 0), 2),
                'volume': coin.get('total_volume', 0),
                'price': coin.get('current_price', 0),
                'market_cap_rank': coin.get('market_cap_rank'),
                'reason': 'بیشترین رشد هفتگی 🚀',
            })
            seen_symbols.add(sym)

    # Add trending
    for coin in trending:
        sym = coin.get('symbol', '').upper()
        if sym and sym not in seen_symbols and sym not in ['USDT', 'USDC', 'BUSD', 'DAI'] and len(watchlist_coins) < 6:
            watchlist_coins.append({
                'symbol': sym,
                'name': coin.get('name'),
                'change_7d': None,
                'volume': None,
                'price': None,
                'market_cap_rank': coin.get('market_cap_rank'),
                'reason': 'ترندینگ هفته 🔥',
            })
            seen_symbols.add(sym)

    # Fill remaining with high volume
    if len(watchlist_coins) < 6:
        high_vol = get_high_volume_coins()
        for coin in high_vol:
            sym = coin.get('symbol', '').upper()
            if sym and sym not in seen_symbols and sym not in ['USDT', 'USDC', 'BUSD', 'DAI'] and len(watchlist_coins) < 6:
                watchlist_coins.append({
                    'symbol': sym,
                    'name': coin.get('name'),
                    'change_7d': round(coin.get('price_change_percentage_7d_in_currency', 0), 2) if coin.get('price_change_percentage_7d_in_currency') else None,
                    'volume': coin.get('total_volume', 0),
                    'price': coin.get('current_price', 0),
                    'market_cap_rank': coin.get('market_cap_rank'),
                    'reason': 'حجم بالای معاملات 📊',
                })
                seen_symbols.add(sym)

    watchlist_coins = watchlist_coins[:6]

    # Return symbols list for inline buttons
    symbols_list = [c['symbol'] for c in watchlist_coins]

    lines.append(f"🎯 *۶ ارز برتر برای واچ این هفته:*\n")

    for i, coin in enumerate(watchlist_coins, 1):
        sym = coin['symbol']
        name = coin['name']
        reason = coin['reason']
        change_7d = coin.get('change_7d')
        price = coin.get('price')
        rank = coin.get('market_cap_rank')

        change_emoji = "📈" if change_7d and change_7d > 0 else "📉" if change_7d and change_7d < 0 else "➡️"
        change_text = f"{change_7d:+.2f}%" if change_7d is not None else "N/A"

        lines.append(f"{'─'*30}")
        lines.append(f"*{i}. {name} ({sym})*")
        if rank:
            lines.append(f"  🏆 رنک: #{rank}")
        if price:
            lines.append(f"  💰 قیمت: ${price:,.4f}")
        lines.append(f"  {change_emoji} تغییر ۷ روزه: {change_text}")
        lines.append(f"  🔍 دلیل انتخاب: {reason}")

        # Technical analysis
        tech = get_technical_score(sym)
        if tech:
            sig_emoji = "🟢" if tech['signal'] == 'LONG' else "🔴" if tech['signal'] == 'SHORT' else "⚪"
            lines.append(f"  {sig_emoji} تکنیکال: {tech['trend']}")
            lines.append(f"  📊 RSI: {tech['rsi']} | سیگنال: {tech['signal']}")
            lines.append(f"  📈 احتمال LONG: {tech['long_pct']}%")
        else:
            lines.append(f"  ⚠️ داده تکنیکال موجود نیست")

        lines.append("")

    # ── Market Summary ──
    lines += [
        f"{'─'*30}",
        f"📉 *بدترین هفته:*",
    ]
    for coin in losers[:2]:
        sym = coin.get('symbol', '').upper()
        change = round(coin.get('price_change_percentage_7d_in_currency', 0), 2)
        lines.append(f"  ❌ {coin.get('name')} ({sym}): {change:+.2f}%")

    lines += [
        f"",
        f"{'─'*30}",
        f"⚠️ این لیست صرفاً تکنیکال و داده‌محور است.",
        f"تحقیق شخصی (DYOR) را فراموش نکنید.",
        f"{'═'*30}",
        f"🕐 آپدیت: {now.strftime('%Y-%m-%d %H:%M')} UTC",
        f"🔄 آپدیت بعدی: دوشنبه آینده",
    ]

    return "\n".join(lines), symbols_list
