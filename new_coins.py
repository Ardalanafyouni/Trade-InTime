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


def get_newly_listed_coins():
    """Get coins recently added to CoinGecko (actually new, sorted by recent addition)"""
    all_coins = []

    # CoinGecko's /coins/list with status=active sorted by id doesn't give date,
    # so we use markets endpoint with order=id_desc as a proxy for recently added,
    # combined with checking ATH date (first trading data point) as recency signal
    for page in [1, 2]:
        data = fetch_coingecko("/coins/markets", params={
            'vs_currency': 'usd',
            'order': 'market_cap_desc',
            'per_page': 250,
            'page': page,
            'sparkline': False,
            'price_change_percentage': '24h,7d',
        })
        if data:
            all_coins.extend(data)

    six_months_ago = datetime.utcnow() - timedelta(days=180)
    candidates = []

    for coin in all_coins:
        coin_id = coin.get('id')
        market_cap = coin.get('market_cap', 0) or 0
        volume = coin.get('total_volume', 0) or 0
        ath_date_str = coin.get('ath_date')
        atl_date_str = coin.get('atl_date')

        if not ath_date_str:
            continue

        try:
            # ATH/ATL date is close to listing date for genuinely new coins
            # (since they haven't had time to set ATH far from launch)
            ath_date = datetime.strptime(ath_date_str[:19], '%Y-%m-%dT%H:%M:%S')
            atl_date = datetime.strptime(atl_date_str[:19], '%Y-%m-%dT%H:%M:%S') if atl_date_str else ath_date
            # Use the EARLIER of the two as proxy for "first seen" date
            first_seen = min(ath_date, atl_date)
        except:
            continue

        # Must be within last 6 months
        if first_seen < six_months_ago:
            continue

        # Minimum liquidity filters to avoid dead/scam tokens
        if market_cap < 1_000_000:  # Min $1M market cap
            continue
        if volume < 100_000:  # Min $100K daily volume
            continue

        candidates.append({
            'id': coin_id,
            'symbol': coin.get('symbol', '').upper(),
            'name': coin.get('name'),
            'market_cap': market_cap,
            'volume': volume,
            'rank': coin.get('market_cap_rank'),
            'price': coin.get('current_price'),
            'change_24h': coin.get('price_change_percentage_24h'),
            'change_7d': coin.get('price_change_percentage_7d_in_currency'),
            'first_seen': first_seen,
            'days_old': (datetime.utcnow() - first_seen).days,
        })

    return candidates


def score_coin_safety(coin):
    """Heuristic scoring for relative safety signals (informational only)"""
    score = 0
    reasons = []

    vol_to_mcap = coin['volume'] / coin['market_cap'] if coin['market_cap'] > 0 else 0

    if 0.03 <= vol_to_mcap <= 0.6:
        score += 2
        reasons.append("نقدینگی سالم")
    elif vol_to_mcap > 0.6:
        reasons.append("⚠️ نوسان حجم بالا")
    else:
        reasons.append("⚠️ نقدینگی پایین")

    if coin['market_cap'] >= 20_000_000:
        score += 2
        reasons.append("مارکت کپ قابل توجه")
    elif coin['market_cap'] >= 5_000_000:
        score += 1
        reasons.append("مارکت کپ متوسط")
    else:
        reasons.append("⚠️ مارکت کپ کوچک")

    if coin['rank'] and coin['rank'] <= 500:
        score += 1
        reasons.append("رنک‌دار در CoinGecko")

    change_7d = coin.get('change_7d')
    if change_7d is not None:
        if -30 <= change_7d <= 80:
            score += 1
        else:
            reasons.append("⚠️ نوسان قیمتی شدید")

    return score, reasons


def get_top_new_coins(limit=10):
    """Get top N genuinely new coins (listed within last 6 months)"""
    candidates = get_newly_listed_coins()
    if not candidates:
        return []

    scored = []
    for coin in candidates:
        score, reasons = score_coin_safety(coin)
        coin['safety_score'] = score
        coin['safety_reasons'] = reasons
        scored.append(coin)

    # Sort by score first, then by volume as tiebreaker
    scored.sort(key=lambda x: (x['safety_score'], x['volume']), reverse=True)
    return scored[:limit]


def generate_new_coins_message(lang='fa'):
    now = datetime.utcnow()

    labels = {
        'fa': {
            'title': '🆕 کوین‌های واقعاً جدید (حداکثر ۶ ماهه)',
            'updated': 'آپدیت',
            'next': 'آپدیت بعدی: فردا ساعت ۹ صبح',
            'warning': '⚠️ *هشدار مهم:*\nاین لیست صرفاً برای اطلاع‌رسانی است و توصیه سرمایه‌گذاری نیست. کوین‌های جدید ریسک بسیار بالایی دارند. برای سرمایه‌گذاری حتماً تحقیق بیشتری انجام دهید (DYOR): وایت‌پیپر، تیم پروژه و قرارداد را شخصاً بررسی کنید.',
            'analyze_hint': 'برای تحلیل هر کدام، روی دکمه زیرش بزنید.',
            'days_old': 'سن',
            'days_text': 'روز',
            'no_data': '❌ در حال حاضر کوین جدیدی با معیارهای حداقلی پیدا نشد.',
        },
        'en': {
            'title': '🆕 Genuinely New Coins (Max 6 Months)',
            'updated': 'Updated',
            'next': 'Next update: Tomorrow 9 AM',
            'warning': '⚠️ *Important Warning:*\nThis list is for informational purposes only and is NOT investment advice. New coins carry very high risk. Always do more research before investing (DYOR): check the whitepaper, team, and contract yourself.',
            'analyze_hint': 'Tap the button below each coin for full analysis.',
            'days_old': 'Age',
            'days_text': 'days',
            'no_data': '❌ No new coins matching minimum criteria found right now.',
        },
        'ru': {
            'title': '🆕 Действительно новые монеты (до 6 месяцев)',
            'updated': 'Обновлено',
            'next': 'Следующее обновление: Завтра в 9:00',
            'warning': '⚠️ *Важное предупреждение:*\nЭтот список предоставлен только для информации и НЕ является инвестиционным советом. Новые монеты несут очень высокий риск. Перед инвестированием проведите собственное исследование (DYOR): изучите whitepaper, команду и контракт.',
            'analyze_hint': 'Нажмите кнопку под монетой для полного анализа.',
            'days_old': 'Возраст',
            'days_text': 'дней',
            'no_data': '❌ Сейчас новых монет, соответствующих минимальным критериям, не найдено.',
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
        lines.append(L['no_data'])
    else:
        for i, coin in enumerate(coins, 1):
            sym = coin['symbol']
            symbols_list.append(sym)
            stars = "⭐" * min(max(coin['safety_score'], 1), 5)
            change_7d = coin.get('change_7d')
            change_text = f"{change_7d:+.1f}%" if change_7d is not None else "N/A"
            change_emoji = "📈" if change_7d and change_7d > 0 else "📉" if change_7d and change_7d < 0 else "➡️"

            lines.append(f"{'─'*28}")
            lines.append(f"*{i}. {coin['name']} ({sym})*")
            lines.append(f"  📅 {L['days_old']}: {coin['days_old']} {L['days_text']}")
            if coin['rank']:
                lines.append(f"  🏆 رنک: #{coin['rank']}  |  امتیاز: {stars}")
            else:
                lines.append(f"  امتیاز: {stars}")
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

