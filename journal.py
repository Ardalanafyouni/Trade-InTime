import json
import os
from datetime import datetime

JOURNAL_FILE = "journals.json"

def load_journals():
    if os.path.exists(JOURNAL_FILE):
        with open(JOURNAL_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_journals(data):
    with open(JOURNAL_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def add_trade(uid, trade):
    data = load_journals()
    uid = str(uid)
    if uid not in data:
        data[uid] = []
    trade['id'] = len(data[uid]) + 1
    trade['date'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M')
    data[uid].append(trade)
    save_journals(data)
    return trade['id']

def get_trades(uid):
    data = load_journals()
    return data.get(str(uid), [])

def delete_trade(uid, trade_id):
    data = load_journals()
    uid = str(uid)
    if uid in data:
        data[uid] = [t for t in data[uid] if t.get('id') != trade_id]
        save_journals(data)

def get_stats(uid):
    trades = get_trades(uid)
    if not trades:
        return None
    closed = [t for t in trades if t.get('status') == 'closed' and t.get('pnl') is not None]
    if not closed:
        return {'total': len(trades), 'closed': 0, 'win': 0, 'loss': 0, 'winrate': 0, 'total_pnl': 0}
    wins = [t for t in closed if t.get('pnl', 0) > 0]
    losses = [t for t in closed if t.get('pnl', 0) <= 0]
    total_pnl = sum(t.get('pnl', 0) for t in closed)
    return {
        'total': len(trades),
        'closed': len(closed),
        'win': len(wins),
        'loss': len(losses),
        'winrate': round(len(wins) / len(closed) * 100) if closed else 0,
        'total_pnl': round(total_pnl, 2)
    }

