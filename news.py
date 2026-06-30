import requests
import logging
import feedparser
from datetime import datetime

logger = logging.getLogger(__name__)

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
    """Fetch latest crypto news from RSS feeds"""
    all_items = []
    feeds = RSS_FEEDS.get(lang, RSS_FEEDS['en'])

    for source_name, url in feeds:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:6]:
                published = entry.get('published_parsed')
                pub_date = datetime(*published[:6]) if published else datetime.utcnow()
                all_items.append({
                    'title': entry.get('title', ''),
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
