import json
import os
from datetime import datetime, timedelta

# Same DATA_DIR convention as journal.py — point this at a Railway Volume
# mount path (e.g. /data) so user records survive redeploys.
DATA_DIR = os.environ.get("DATA_DIR", ".")
os.makedirs(DATA_DIR, exist_ok=True)
USERS_FILE = os.path.join(DATA_DIR, "users.json")

DATE_FMT = "%Y-%m-%d %H:%M:%S"


def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_users(data):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def track_user(uid, username=None, first_name=None, started=False):
    """Record/update a user. Writes to disk only when something meaningful
    changed (new user, new day, profile change, or newly started) to avoid
    a disk write on every single message. last_seen has day-level precision,
    which is enough for the daily/weekly stats this module reports."""
    data = load_users()
    uid = str(uid)
    now = datetime.utcnow()
    now_str = now.strftime(DATE_FMT)
    today = now.strftime("%Y-%m-%d")

    if uid not in data:
        data[uid] = {
            'username': username or '',
            'first_name': first_name or '',
            'first_seen': now_str,
            'last_seen': now_str,
            'visit_days': 1,
            'started': bool(started),
        }
        save_users(data)
        return data[uid]

    record = data[uid]
    changed = False

    if username and record.get('username') != username:
        record['username'] = username
        changed = True
    if first_name and record.get('first_name') != first_name:
        record['first_name'] = first_name
        changed = True
    if started and not record.get('started'):
        record['started'] = True
        changed = True

    if (record.get('last_seen') or '')[:10] != today:
        record['last_seen'] = now_str
        record['visit_days'] = record.get('visit_days', 0) + 1
        changed = True

    if changed:
        save_users(data)
    return record


def get_all_users():
    return load_users()


def get_user_stats():
    data = load_users()
    now = datetime.utcnow()
    today = now.strftime("%Y-%m-%d")
    week_ago = now - timedelta(days=7)

    total = len(data)
    started_count = sum(1 for u in data.values() if u.get('started'))
    new_today = sum(1 for u in data.values() if (u.get('first_seen') or '')[:10] == today)
    active_today = sum(1 for u in data.values() if (u.get('last_seen') or '')[:10] == today)

    new_week = active_week = 0
    for u in data.values():
        try:
            if datetime.strptime(u.get('first_seen', '1970-01-01 00:00:00'), DATE_FMT) >= week_ago:
                new_week += 1
        except ValueError:
            pass
        try:
            if datetime.strptime(u.get('last_seen', '1970-01-01 00:00:00'), DATE_FMT) >= week_ago:
                active_week += 1
        except ValueError:
            pass

    return {
        'total': total,
        'started_count': started_count,
        'new_today': new_today,
        'active_today': active_today,
        'new_week': new_week,
        'active_week': active_week,
    }


def generate_users_report(lang='fa', recent_n=10):
    stats = get_user_stats()
    data = load_users()

    labels = {
        'fa': {
            'title': '📊 آمار کاربران ربات', 'total': '👥 کل کاربران', 'started': '✅ استارت‌کرده‌ها',
            'new_today': '🆕 جدید امروز', 'active_today': '🟢 فعال امروز',
            'new_week': '🆕 جدید (۷ روز اخیر)', 'active_week': '🟢 فعال (۷ روز اخیر)',
            'recent': 'آخرین کاربران:', 'no_users': 'هنوز کاربری ثبت نشده.',
            'no_username': 'بدون یوزرنیم',
        },
        'en': {
            'title': '📊 Bot User Stats', 'total': '👥 Total users', 'started': '✅ Started /start',
            'new_today': '🆕 New today', 'active_today': '🟢 Active today',
            'new_week': '🆕 New (7d)', 'active_week': '🟢 Active (7d)',
            'recent': 'Most recent users:', 'no_users': 'No users recorded yet.',
            'no_username': 'no username',
        },
        'ru': {
            'title': '📊 Статистика пользователей', 'total': '👥 Всего пользователей', 'started': '✅ Нажали /start',
            'new_today': '🆕 Новые сегодня', 'active_today': '🟢 Активны сегодня',
            'new_week': '🆕 Новые (7д)', 'active_week': '🟢 Активны (7д)',
            'recent': 'Последние пользователи:', 'no_users': 'Пользователи пока не зарегистрированы.',
            'no_username': 'без юзернейма',
        },
    }
    L = labels.get(lang, labels['en'])

    lines = [
        L['title'], "─" * 24,
        f"{L['total']}: {stats['total']}",
        f"{L['started']}: {stats['started_count']}",
        f"{L['new_today']}: {stats['new_today']}",
        f"{L['active_today']}: {stats['active_today']}",
        f"{L['new_week']}: {stats['new_week']}",
        f"{L['active_week']}: {stats['active_week']}",
    ]

    if data:
        lines += ["", L['recent']]
        recent = sorted(data.items(), key=lambda kv: kv[1].get('first_seen', ''), reverse=True)[:recent_n]
        for uid, u in recent:
            uname = f"@{u['username']}" if u.get('username') else L['no_username']
            name = u.get('first_name') or ''
            lines.append(f"• {uname} {name} — {u.get('first_seen', '?')[:10]}")
    else:
        lines += ["", L['no_users']]

    return "\n".join(lines)
