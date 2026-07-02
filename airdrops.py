import logging
import feedparser
from datetime import datetime, timedelta

from news import translate_text  # reuse the existing translation helper

logger = logging.getLogger(__name__)

# AirdropAlert has been curating/verifying airdrop listings since 2017 and
# publishes each new listing as an RSS post the day it goes live, so the
# post's publish date is a solid proxy for "airdrop start date".
AIRDROP_FEEDS = [
    ("AirdropAlert", "https://airdropalert.com/feed/rssfeed"),
]

MAX_AGE_DAYS = 60  # "حداکثر ۲ ماه پیش"

SEASON_KEYWORDS = [
    'season 2', 'season 3', 'season 4', 'season 5', 'new season',
    'season two', 'season three', 'next season', 'phase 2', 'phase 3',
    'round 2', 'round 3',
]

# Titles/links containing these are cleanup/meta posts, not real airdrop
# listings, and are filtered out.
NOISE_KEYWORDS = ['unclaimed', 'how to', 'guide to', 'best airdrops of']


def is_fresh_season(title):
    t = title.lower()
    return any(kw in t for kw in SEASON_KEYWORDS)


def is_noise(title):
    t = title.lower()
    return any(kw in t for kw in NOISE_KEYWORDS)


def fetch_airdrops(limit=40):
    """Fetch airdrop listings published within the last MAX_AGE_DAYS days."""
    cutoff = datetime.utcnow() - timedelta(days=MAX_AGE_DAYS)
    items = []

    for source_name, url in AIRDROP_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                published = entry.get('published_parsed') or entry.get('updated_parsed')
                if not published:
                    continue
                pub_date = datetime(*published[:6])
                if pub_date < cutoff:
                    continue

                title = entry.get('title', '').strip()
                if not title or is_noise(title):
                    continue

                items.append({
                    'title': title,
                    'link': entry.get('link', ''),
                    'source': source_name,
                    'published': pub_date,
                    'is_new_season': is_fresh_season(title),
                    'days_ago': (datetime.utcnow() - pub_date).days,
                })
        except Exception as e:
            logger.error(f"Airdrop RSS fetch error for {source_name}: {e}")
            continue

    # De-duplicate by link, keep newest first
    seen_links = set()
    unique_items = []
    for item in sorted(items, key=lambda x: x['published'], reverse=True):
        if item['link'] in seen_links:
            continue
        seen_links.add(item['link'])
        unique_items.append(item)

    return unique_items[:limit]


LABELS = {
    'fa': {
        'title': '🎁 ایردراپ‌های معتبر (حداکثر ۲ ماه اخیر)',
        'season_title': '🔥 سیزن‌های تازه',
        'regular_title': '🆕 ایردراپ‌های جدید',
        'updated': 'آپدیت',
        'no_data': '❌ در حال حاضر ایردراپ معتبری با این معیارها پیدا نشد.',
        'days_ago': 'روز پیش',
        'today': 'امروز',
        'warning': '⚠️ *هشدار:* این لیست صرفاً جنبه اطلاع‌رسانی دارد. قبل از اتصال کیف‌پول یا انجام هر تسکی، خودتان پروژه را بررسی کنید (DYOR) و هرگز سیدفریز یا پرایوت‌کی را در هیچ سایتی وارد نکنید.',
    },
    'en': {
        'title': '🎁 Verified Airdrops (Last 2 Months)',
        'season_title': '🔥 Fresh Seasons',
        'regular_title': '🆕 New Airdrops',
        'updated': 'Updated',
        'no_data': '❌ No verified airdrops matching these criteria right now.',
        'days_ago': 'days ago',
        'today': 'today',
        'warning': '⚠️ *Warning:* This list is for informational purposes only. Always DYOR before connecting a wallet or completing any task, and never enter your seed phrase or private key on any site.',
    },
    'ru': {
        'title': '🎁 Проверенные аирдропы (за последние 2 месяца)',
        'season_title': '🔥 Новые сезоны',
        'regular_title': '🆕 Новые аирдропы',
        'updated': 'Обновлено',
        'no_data': '❌ Проверенных аирдропов по этим критериям сейчас не найдено.',
        'days_ago': 'дней назад',
        'today': 'сегодня',
        'warning': '⚠️ *Внимание:* Этот список предоставлен только для информации. Всегда проводите собственное исследование (DYOR) перед подключением кошелька и никогда не вводите seed-фразу или приватный ключ на сторонних сайтах.',
    },
}


def _format_item(item, lang, labels):
    title = translate_text(item['title'], lang) if lang != 'en' else item['title']
    age_text = labels['today'] if item['days_ago'] == 0 else f"{item['days_ago']} {labels['days_ago']}"
    prefix = "🔥 " if item['is_new_season'] else ""
    lines = [
        f"{prefix}*{title}*",
        f"   📅 {age_text}  |  📡 {item['source']}",
        f"   🔗 {item['link']}",
        "",
    ]
    return lines


def generate_airdrops_message(lang='fa'):
    labels = LABELS.get(lang, LABELS['en'])
    now = datetime.utcnow()
    items = fetch_airdrops(limit=40)

    lines = [
        f"{'═'*28}",
        f"  {labels['title']}",
        f"{'═'*28}",
        "",
        labels['warning'],
        "",
    ]

    if not items:
        lines.append(labels['no_data'])
    else:
        season_items = [i for i in items if i['is_new_season']]
        regular_items = [i for i in items if not i['is_new_season']]

        if season_items:
            lines.append(f"*{labels['season_title']}*")
            lines.append(f"{'─'*28}")
            for item in season_items[:10]:
                lines.extend(_format_item(item, lang, labels))

        if regular_items:
            lines.append(f"*{labels['regular_title']}*")
            lines.append(f"{'─'*28}")
            for item in regular_items[:20]:
                lines.extend(_format_item(item, lang, labels))

    lines += [
        f"{'─'*28}",
        f"🔄 {labels['updated']}: {now.strftime('%Y-%m-%d %H:%M')} UTC",
    ]

    return "\n".join(lines)
