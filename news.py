import requests
import logging
import feedparser
from datetime import datetime

logger = logging.getLogger(__name__)


def translate_text(text, target_lang='fa'):
    """Translate text using free Google Translate endpoint"""
    if target_lang == 'en':
        return text
    try:
        url = "https://translate.googleapis.com/translate_a/single"
        params = {
            'client': 'gtx',
            'sl': 'en',
            'tl': target_lang,
            'dt': 't',
            'q': text,
        }
        r = requests.get(url, params=params, timeout=8)
        r.raise_for_status()
        result = r.json()
        translated = ''.join([seg[0] for seg in result[0] if seg[0]])
        return translated
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return text

RSS_FEEDS = {
    'fa': [
        ('CoinDesk', 'https://www.coindesk.com/arc/outboundfeeds/rss/'),
        ('Cointelegraph', 'https://cointelegraph.com/rss'),
    ],
    'en': [
        ('CoinDesk', 'https://www.coindesk.com/arc/outboundfeeds/rss/'),
        ('Cointelegraph', 'https://cointelegraph.com/rss'),
    ],
    'ru': [
        ('CoinDesk', 'https://www.coindesk.com/arc/outboundfeeds/rss/'),
        ('Cointelegraph', 'https://cointelegraph.com/rss'),
    ],
}

LABELS = {
    'fa': {'title': '📰 اخبار داغ کریپتو', 'updated': 'آپدیت', 'source': 'منبع', 'no_news': 'خبری یافت نشد.'},
    'en': {'title': '📰 Latest Crypto News', 'updated': 'Updated', 'source': 'Source', 'no_news': 'No news found.'},
    'ru': {'title': '📰 Последние новости крипто', 'updated': 'Обновлено', 'source': 'Источник', 'no_news': 'Новостей не найдено.'},
}


def fetch_news(lang='fa', limit=8):
    """Fetch latest crypto news from RSS feeds (always in English) and translate"""
    all_items = []
    feeds = RSS_FEEDS.get('en', RSS_FEEDS['en'])

    for source_name, url in feeds:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:6]:
                published = entry.get('published_parsed')
                pub_date = datetime(*published[:6]) if published else datetime.utcnow()
                title = entry.get('title', '')
                translated_title = translate_text(title, lang) if lang != 'en' else title
                all_items.append({
                    'title': translated_title,
                    'original_title': title,
                    'link': entry.get('link', ''),
                    'source': source_name,
                    'published': pub_date,
                })
        except Exception as e:
            logger.error(f"RSS fetch error for {source_name}: {e}")
            continue

    all_items.sort(key=lambda x: x['published'], reverse=True)
    return all_items[:limit]


def generate_news_message(lang='fa'):
    labels = LABELS.get(lang, LABELS['en'])
    news_items = fetch_news(lang, limit=8)

    now = datetime.utcnow()
    lines = [
        f"{'═'*28}",
        f"  {labels['title']}",
        f"{'═'*28}",
        f"",
    ]

    if not news_items:
        lines.append(labels['no_news'])
    else:
        for i, item in enumerate(news_items, 1):
            time_ago = now - item['published']
            hours = int(time_ago.total_seconds() // 3600)
            time_text = f"{hours}h ago" if hours > 0 else "just now"

            lines.append(f"*{i}.* {item['title']}")
            lines.append(f"   📡 {item['source']} • ⏱ {time_text}")
            lines.append(f"   🔗 {item['link']}")
            lines.append("")

    lines += [
        f"{'─'*28}",
        f"🔄 {labels['updated']}: {now.strftime('%Y-%m-%d %H:%M')} UTC",
        f"⏰ آپدیت بعدی: ۱ ساعت دیگر",
    ]

    return "\n".join(lines)
