import requests
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

COINGECKO_BASE = "https://api.coingecko.com/api/v3"


def fetch_coingecko(endpoint, params=None):
    try:
        r = requests.get(f"{COINGECKO_BASE}{endpoint}", params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.error(f"CoinGecko error: {e}")
        return None


def get_recently_listed_coins():
    """Get coins recently added to CoinGecko with decent market presence"""
    # Get coins sorted by market cap to filter for legitimacy
    data = fetch_coingecko("/coins/markets", params={
        'vs_currency': 'usd',
        'order': 'market_cap_desc',
        'per_page': 250,
        'page': 1,
        'sparkline': False,
        'price_change_percentage': '24h,7d',
    })
    if not data:
        return []

    candidates = []
    for coin in data:
        market_cap = coin.get('market_cap', 0) or 0
        volume = coin.get('total_volume', 0) or 0
        rank = coin.get('market_cap_rank')

        # Filter criteria for "safer" new coins:
        # - Has meaningful market cap (not a ghost token)
        # - Has real trading volume (liquidity exists)
        # - Ranked (meaning it's tracked and somewhat established)
        # - Volume/MarketCap ratio shows active trading, not just listed
        if not rank or rank > 500:
            continue
        if market_cap < 5_000_000:  # Min $5M market cap
            continue
        if volume < 500_000:  # Min $500K daily volume
            continue

        vol_to_mcap = volume / market_cap if market_cap > 0 else 0

        candidates.append({
            'id': coin.get('id'),
            'symbol': coin.get('symbol', '').upper(),
            'name': coin.get('name'),
            'market_cap': market_cap,
            'volume': volume,
            'rank': rank,
            'price': coin.get('current_price'),
            'change_24h': coin.get('price_change_percentage_24h'),
            'change_7d': coin.get('price_change_percentage_7d_in_currency'),
            'vol_to_mcap': vol_to_mcap,
            'ath_date': coin.get('ath_date'),
        })

    return candidates


def score_coin_safety(coin):
    """Simple heuristic scoring for relative safety signals (not financial advice)"""
    score = 0
    reasons = []

    # Higher rank = more established = safer signal
    if coin['rank'] <= 100:
        score += 3
        reasons.append("رنک بالای ۱۰۰")
    elif coin['rank'] <= 300:
        score += 2
        reasons.append("رنک معتبر")
    else:
        score += 1

    # Healthy volume/mcap ratio (not too low = illiquid, not too high = pump)
    vtm = coin['vol_to_mcap']
    if 0.05 <= vtm <= 0.5:
        score += 2
        reasons.append("نقدینگی سالم")
    elif vtm > 0.5:
        score += 0
        reasons.append("⚠️ نوسان حجم بالا")
    else:
        score += 1

    # Stable-ish growth not extreme pump
    change_7d = coin.get('change_7d')
    if change_7d is not None:
        if -20 <= change_7d <= 50:
            score += 2
            reasons.append("رشد متعادل")
        elif change_7d > 50:
            reasons.append("⚠️ رشد بسیار سریع (احتمال پامپ)")
        else:
            reasons.append("⚠️ افت قیمت اخیر")

    # Market cap tier
    if coin['market_cap'] >= 50_000_000:
        score += 2
        reasons.append("مارکت کپ قابل توجه")
    elif coin['market_cap'] >= 20_000_000:
        score += 1

    return score, reasons


def get_top_new_coins(limit=10):
    """Get top N relatively-safer new/emerging coins"""
    candidates = get_recently_listed_coins()
    if not candidates:
        return []

    scored = []
    for coin in candidates:
        score, reasons = score_coin_safety(coin)
        coin['safety_score'] = score
        coin['safety_reasons'] = reasons
        scored.append(coin)

    scored.sort(key=lambda x: x['safety_score'], reverse=True)
    return scored[:limit]


def generate_new_coins_message(lang='fa'):
    now = datetime.utcnow()

    labels = {
        'fa': {
            'title': '🆕 کوین‌های نوظهور — لیست روزانه',
            'updated': 'آپدیت',
            'next': 'آپدیت بعدی: فردا ساعت ۹ صبح',
            'warning': '⚠️ *هشدار مهم:*\nاین لیست بر اساس داده‌های بازار (حجم، نقدینگی، رنک) تهیه شده و به معنای تایید یا توصیه نیست. کوین‌های جدید ریسک بسیار بالایی دارند. همیشه وایت‌پیپر، تیم پروژه و قرارداد را شخصاً بررسی کنید (DYOR).',
            'analyze_hint': 'برای تحلیل هر کدام، نام آن را به /analyze بفرستید.',
        },
        'en': {
            'title': '🆕 Emerging Coins — Daily List',
            'updated': 'Updated',
            'next': 'Next update: Tomorrow 9 AM',
            'warning': '⚠️ *Important Warning:*\nThis list is based on market data (volume, liquidity, rank) only — not investment advice. New coins carry very high risk. Always research the whitepaper, team, and contract yourself (DYOR).',
            'analyze_hint': 'Use /analyze with any symbol to get full technical analysis.',
        },
        'ru': {
            'title': '🆕 Новые монеты — Ежедневный список',
            'updated': 'Обновлено',
            'next': 'Следующее обновление: Завтра в 9:00',
            'warning': '⚠️ *Важное предупреждение:*\nЭтот список основан только на рыночных данных (объём, ликвидность, ранг) — не является финансовым советом. Новые монеты несут очень высокий риск. Всегда изучайте whitepaper, команду и контракт самостоятельно (DYOR).',
            'analyze_hint': 'Используйте /analyze с любым символом для полного технического анализа.',
        },
    }
    L = labels.get(lang, labels['en'])

    lines = [
        f"{'═'*28}",
        f"  {L['title']}",
        f"  {now.strftime('%Y-%m-%d')}",
        f"{'═'*28}",
        f"",
        L['warning'],
        f"",
    ]

    coins = get_top_new_coins(limit=10)
    symbols_list = []

    if not coins:
        lines.append("❌ داده‌ای یافت نشد.")
    else:
        for i, coin in enumerate(coins, 1):
            sym = coin['symbol']
            symbols_list.append(sym)
            stars = "⭐" * min(coin['safety_score'], 5)
            change_7d = coin.get('change_7d')
            change_text = f"{change_7d:+.1f}%" if change_7d is not None else "N/A"
            change_emoji = "📈" if change_7d and change_7d > 0 else "📉" if change_7d and change_7d < 0 else "➡️"

            lines.append(f"{'─'*28}")
            lines.append(f"*{i}. {coin['name']} ({sym})*")
            lines.append(f"  🏆 رنک: #{coin['rank']}  |  امتیاز: {stars}")
            lines.append(f"  💰 قیمت: ${coin['price']:,.6f}" if coin['price'] else "  💰 قیمت: N/A")
            lines.append(f"  📊 مارکت کپ: ${coin['market_cap']:,.0f}")
            lines.append(f"  {change_emoji} تغییر ۷ روزه: {change_text}")
            lines.append(f"  🔍 {' | '.join(coin['safety_reasons'][:3])}")
            lines.append("")

    lines += [
        f"{'─'*28}",
        L['analyze_hint'],
        f"",
        f"{'─'*28}",
        f"🔄 {L['updated']}: {now.strftime('%Y-%m-%d %H:%M')} UTC",
        f"⏰ {L['next']}",
    ]

    return "\n".join(lines), symbols_list

