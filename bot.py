import os
import logging
from io import BytesIO
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler, filters, ContextTypes
)

from analyzer import CryptoAnalyzer
from chart_generator import generate_chart
from terms import TERMS, TERM_ALIASES, ALL_TERMS_FA, ALL_TERMS_EN, ALL_TERMS_RU
from journal import add_trade, get_trades, delete_trade, get_stats

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ── States ──
WAITING_SYMBOL, WAITING_TIMEFRAME = range(2)
(J_SYMBOL, J_DIRECTION, J_ENTRY, J_SL, J_TP, J_SIZE, J_NOTE,
 J_CLOSE_ID, J_CLOSE_EXIT, J_CLOSE_PNL) = range(10, 20)

TEXTS = {
    'fa': {
        'welcome': "👋 *سلام! ربات تحلیل و ژورنال کریپتو*\n\n/analyze - تحلیل + چارت\n/journal - ژورنال معاملات\n/terms - اصطلاحات\n/lang - زبان",
        'enter_symbol': "🪙 نام ارز را وارد کنید:\nمثال: `BTC`, `ETH`, `SOL`",
        'choose_tf': "تایم‌فریم را انتخاب کنید:",
        'analyzing': "⏳ در حال تحلیل و رسم چارت",
        'error': "❌ خطا:", 'cancel': "❌ لغو شد.",
        'term_not_found': "❓ اصطلاح پیدا نشد. /terms را بزنید.",
        'choose_lang': "🌐 زبان را انتخاب کنید:",
        'lang_set': "✅ زبان فارسی انتخاب شد.",
        'timeframes': {"1m": "1 دقیقه", "5m": "5 دقیقه", "15m": "15 دقیقه",
                       "1h": "1 ساعت", "4h": "4 ساعت", "1d": "روزانه", "1w": "هفتگی"},
    },
    'en': {
        'welcome': "👋 *Crypto Analysis & Journal Bot*\n\n/analyze - Analysis + Chart\n/journal - Trade Journal\n/terms - Terms\n/lang - Language",
        'enter_symbol': "🪙 Enter coin symbol:\nExample: `BTC`, `ETH`, `SOL`",
        'choose_tf': "Select timeframe:",
        'analyzing': "⏳ Analyzing and generating chart",
        'error': "❌ Error:", 'cancel': "❌ Cancelled.",
        'term_not_found': "❓ Term not found. Use /terms",
        'choose_lang': "🌐 Choose your language:",
        'lang_set': "✅ English selected.",
        'timeframes': {"1m": "1 Min", "5m": "5 Min", "15m": "15 Min",
                       "1h": "1 Hour", "4h": "4 Hour", "1d": "Daily", "1w": "Weekly"},
    },
    'ru': {
        'welcome': "👋 *Бот анализа и журнала крипто*\n\n/analyze - Анализ + График\n/journal - Журнал сделок\n/terms - Термины\n/lang - Язык",
        'enter_symbol': "🪙 Введите символ:\nПример: `BTC`, `ETH`, `SOL`",
        'choose_tf': "Выберите таймфрейм:",
        'analyzing': "⏳ Анализирую и строю график",
        'error': "❌ Ошибка:", 'cancel': "❌ Отменено.",
        'term_not_found': "❓ Термин не найден. /terms",
        'choose_lang': "🌐 Выберите язык:",
        'lang_set': "✅ Русский выбран.",
        'timeframes': {"1m": "1 Мин", "5m": "5 Мин", "15m": "15 Мин",
                       "1h": "1 Час", "4h": "4 Часа", "1d": "День", "1w": "Неделя"},
    }
}

analyzer = CryptoAnalyzer()
user_langs = {}

def get_lang(uid): return user_langs.get(uid, 'fa')
def t(uid, key): return TEXTS[get_lang(uid)][key]


# ─────────────────────────────────────────────
# EXCEL EXPORT
# ─────────────────────────────────────────────

def export_to_excel(uid, lang='fa'):
    trades = get_trades(uid)
    stats = get_stats(uid)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Trade Journal"

    # Colors
    dark_bg = "1E222D"
    header_bg = "2962FF"
    green_bg = "1B5E20"
    red_bg = "B71C1C"
    alt_bg = "1A1E2E"

    headers_map = {
        'fa': ['#', 'تاریخ', 'ارز', 'جهت', 'ورود', 'حد ضرر', 'تارگت', 'حجم', 'خروج', 'P&L ($)', 'وضعیت', 'یادداشت'],
        'en': ['#', 'Date', 'Symbol', 'Direction', 'Entry', 'Stop Loss', 'Take Profit', 'Size', 'Exit', 'P&L ($)', 'Status', 'Note'],
        'ru': ['#', 'Дата', 'Символ', 'Направление', 'Вход', 'Стоп-лосс', 'Тейк-профит', 'Объём', 'Выход', 'P&L ($)', 'Статус', 'Заметка'],
    }
    headers = headers_map.get(lang, headers_map['en'])
    col_widths = [5, 18, 10, 10, 12, 12, 12, 10, 12, 12, 10, 25]

    # Title row
    ws.merge_cells('A1:L1')
    title_cell = ws['A1']
    title_cell.value = f"📊 Trade Journal — {datetime.utcnow().strftime('%Y-%m-%d')}"
    title_cell.font = Font(bold=True, size=14, color="FFFFFF")
    title_cell.fill = PatternFill("solid", fgColor=header_bg)
    title_cell.alignment = Alignment(horizontal='center', vertical='center')
    ws.row_dimensions[1].height = 30

    # Stats row
    if stats:
        ws.merge_cells('A2:L2')
        stat_text = f"Total: {stats['total']} | Closed: {stats['closed']} | Win: {stats['win']} | Loss: {stats['loss']} | Winrate: {stats['winrate']}% | Total P&L: {stats['total_pnl']}$"
        stat_cell = ws['A2']
        stat_cell.value = stat_text
        stat_cell.font = Font(bold=True, size=10, color="FFFFFF")
        stat_cell.fill = PatternFill("solid", fgColor="263238")
        stat_cell.alignment = Alignment(horizontal='center', vertical='center')
        ws.row_dimensions[2].height = 22

    # Headers
    header_row = 3
    for col, (header, width) in enumerate(zip(headers, col_widths), 1):
        cell = ws.cell(row=header_row, column=col, value=header)
        cell.font = Font(bold=True, size=10, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="37474F")
        cell.alignment = Alignment(horizontal='center', vertical='center')
        ws.column_dimensions[get_column_letter(col)].width = width
    ws.row_dimensions[header_row].height = 20

    # Data rows
    thin = Side(style='thin', color='2A2E39')
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    for row_idx, trade in enumerate(trades, header_row + 1):
        is_alt = row_idx % 2 == 0
        row_bg = alt_bg if is_alt else dark_bg

        pnl = trade.get('pnl')
        if pnl is not None:
            if pnl > 0:
                row_bg = "1B3A1B"
            elif pnl < 0:
                row_bg = "3A1B1B"

        direction = trade.get('direction', '')
        dir_color = "00E676" if direction in ['LONG', 'لانگ', 'Long'] else "FF5252"

        values = [
            trade.get('id', ''),
            trade.get('date', ''),
            trade.get('symbol', ''),
            direction,
            trade.get('entry', ''),
            trade.get('sl', ''),
            trade.get('tp', ''),
            trade.get('size', ''),
            trade.get('exit_price', ''),
            trade.get('pnl', ''),
            trade.get('status', 'open'),
            trade.get('note', ''),
        ]

        for col, value in enumerate(values, 1):
            cell = ws.cell(row=row_idx, column=col, value=value)
            cell.fill = PatternFill("solid", fgColor=row_bg)
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.border = border
            cell.font = Font(color="FFFFFF", size=9)

            if col == 4:  # Direction
                cell.font = Font(color=dir_color, bold=True, size=9)
            if col == 10 and pnl is not None:  # P&L
                color = "00E676" if pnl > 0 else "FF5252"
                cell.font = Font(color=color, bold=True, size=9)

        ws.row_dimensions[row_idx].height = 18

    # Freeze header
    ws.freeze_panes = f'A{header_row + 1}'

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


# ─────────────────────────────────────────────
# JOURNAL HANDLERS
# ─────────────────────────────────────────────

async def journal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    trades = get_trades(uid)
    stats = get_stats(uid)

    keyboard = [
        [InlineKeyboardButton("➕ ثبت معامله جدید", callback_data="j_new"),
         InlineKeyboardButton("📋 لیست معاملات", callback_data="j_list")],
        [InlineKeyboardButton("✅ بستن معامله", callback_data="j_close"),
         InlineKeyboardButton("📊 آمار", callback_data="j_stats")],
        [InlineKeyboardButton("📥 اکسپورت اکسل", callback_data="j_export")],
    ]

    text = "📒 *ژورنال معاملات*\n\n"
    if stats:
        text += f"• تعداد کل: {stats['total']}\n"
        text += f"• بسته شده: {stats['closed']}\n"
        text += f"• وین ریت: {stats['winrate']}%\n"
        text += f"• سود/زیان کل: {stats['total_pnl']}$\n"
    else:
        text += "هنوز معامله‌ای ثبت نشده."

    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


async def journal_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    data = query.data

    if data == "j_new":
        await query.message.reply_text("🪙 نماد ارز را وارد کنید:\nمثال: `BTC`", parse_mode="Markdown")
        return J_SYMBOL

    elif data == "j_list":
        trades = get_trades(uid)
        if not trades:
            await query.message.reply_text("📋 هیچ معامله‌ای ثبت نشده.")
            return

        text = "📋 *آخرین معاملات:*\n\n"
        for trade in trades[-10:]:
            status = trade.get('status', 'open')
            pnl = trade.get('pnl')
            pnl_text = f" | P&L: {pnl}$" if pnl is not None else ""
            emoji = "🟢" if status == 'closed' and pnl and pnl > 0 else "🔴" if status == 'closed' else "🟡"
            text += f"{emoji} #{trade['id']} {trade.get('symbol')} {trade.get('direction')} @ {trade.get('entry')}{pnl_text}\n"
            text += f"   📅 {trade.get('date')}\n\n"

        await query.message.reply_text(text, parse_mode="Markdown")

    elif data == "j_stats":
        stats = get_stats(uid)
        if not stats:
            await query.message.reply_text("📊 هنوز آماری موجود نیست.")
            return
        text = (
            f"📊 *آمار معاملات:*\n\n"
            f"• کل: {stats['total']}\n"
            f"• بسته: {stats['closed']}\n"
            f"• ✅ برنده: {stats['win']}\n"
            f"• ❌ بازنده: {stats['loss']}\n"
            f"• 🎯 وین ریت: {stats['winrate']}%\n"
            f"• 💰 سود/زیان کل: {stats['total_pnl']}$"
        )
        await query.message.reply_text(text, parse_mode="Markdown")

    elif data == "j_export":
        lang = get_lang(uid)
        buf = export_to_excel(uid, lang)
        filename = f"journal_{datetime.utcnow().strftime('%Y%m%d')}.xlsx"
        await query.message.reply_document(document=buf, filename=filename, caption="📥 فایل اکسل ژورنال شما")

    elif data == "j_close":
        trades = get_trades(uid)
        open_trades = [t for t in trades if t.get('status') == 'open']
        if not open_trades:
            await query.message.reply_text("هیچ معامله بازی وجود ندارد.")
            return
        text = "کدام معامله را میخواهید ببندید؟\n\n"
        for t in open_trades[-5:]:
            text += f"#{t['id']} {t.get('symbol')} {t.get('direction')} @ {t.get('entry')}\n"
        text += "\nشماره معامله را وارد کنید:"
        await query.message.reply_text(text)
        return J_CLOSE_ID


async def j_symbol(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['j_symbol'] = update.message.text.strip().upper()
    keyboard = [[
        InlineKeyboardButton("📈 LONG", callback_data="jd_long"),
        InlineKeyboardButton("📉 SHORT", callback_data="jd_short"),
    ]]
    await update.message.reply_text("جهت معامله:", reply_markup=InlineKeyboardMarkup(keyboard))
    return J_DIRECTION

async def j_direction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['j_direction'] = "LONG" if query.data == "jd_long" else "SHORT"
    await query.message.reply_text("💰 قیمت ورود را وارد کنید:")
    return J_ENTRY

async def j_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['j_entry'] = update.message.text.strip()
    await update.message.reply_text("🛑 حد ضرر (Stop Loss) را وارد کنید:")
    return J_SL

async def j_sl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['j_sl'] = update.message.text.strip()
    await update.message.reply_text("🎯 تارگت (Take Profit) را وارد کنید:")
    return J_TP

async def j_tp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['j_tp'] = update.message.text.strip()
    await update.message.reply_text("📦 حجم معامله (مثلاً 100$) را وارد کنید:")
    return J_SIZE

async def j_size(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['j_size'] = update.message.text.strip()
    await update.message.reply_text("📝 یادداشت (اختیاری - یا /skip بزنید):")
    return J_NOTE

async def j_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    note = "" if update.message.text.strip() == '/skip' else update.message.text.strip()
    trade = {
        'symbol': context.user_data.get('j_symbol'),
        'direction': context.user_data.get('j_direction'),
        'entry': context.user_data.get('j_entry'),
        'sl': context.user_data.get('j_sl'),
        'tp': context.user_data.get('j_tp'),
        'size': context.user_data.get('j_size'),
        'note': note,
        'status': 'open',
        'exit_price': None,
        'pnl': None,
    }
    trade_id = add_trade(uid, trade)
    await update.message.reply_text(
        f"✅ *معامله #{trade_id} ثبت شد!*\n\n"
        f"• {trade['symbol']} {trade['direction']}\n"
        f"• ورود: {trade['entry']}\n"
        f"• SL: {trade['sl']}\n"
        f"• TP: {trade['tp']}\n"
        f"• حجم: {trade['size']}",
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def j_close_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data['j_close_id'] = int(update.message.text.strip())
        await update.message.reply_text("💰 قیمت خروج را وارد کنید:")
        return J_CLOSE_EXIT
    except:
        await update.message.reply_text("❌ شماره نامعتبر.")
        return ConversationHandler.END

async def j_close_exit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['j_close_exit'] = update.message.text.strip()
    await update.message.reply_text("📊 سود/زیان (P&L) به دلار وارد کنید:\nمثال: `+150` یا `-80`")
    return J_CLOSE_PNL

async def j_close_pnl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    try:
        pnl = float(update.message.text.strip().replace('+', ''))
        trade_id = context.user_data.get('j_close_id')
        trades = get_trades(uid)
        from journal import load_journals, save_journals
        data = load_journals()
        for trade in data.get(str(uid), []):
            if trade.get('id') == trade_id:
                trade['status'] = 'closed'
                trade['exit_price'] = context.user_data.get('j_close_exit')
                trade['pnl'] = pnl
                break
        save_journals(data)
        emoji = "✅ سود" if pnl > 0 else "❌ ضرر"
        await update.message.reply_text(f"{emoji}: {pnl}$\nمعامله #{trade_id} بسته شد.")
    except:
        await update.message.reply_text("❌ مقدار نامعتبر.")
    return ConversationHandler.END


# ─────────────────────────────────────────────
# ANALYZE HANDLERS
# ─────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    await update.message.reply_text(t(uid, 'welcome'), parse_mode="Markdown")

async def lang_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    keyboard = [[
        InlineKeyboardButton("🇮🇷 فارسی", callback_data="lang_fa"),
        InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
        InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
    ]]
    await update.message.reply_text(t(uid, 'choose_lang'), reply_markup=InlineKeyboardMarkup(keyboard))

async def set_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    lang = query.data.split('_')[1]
    user_langs[uid] = lang
    await query.edit_message_text(TEXTS[lang]['lang_set'])

async def terms_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = get_lang(uid)
    msg = ALL_TERMS_FA if lang == 'fa' else ALL_TERMS_EN if lang == 'en' else ALL_TERMS_RU
    await update.message.reply_text(msg, parse_mode="Markdown")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = get_lang(uid)
    text = update.message.text.strip().lower()
    term_key = TERM_ALIASES.get(text) or TERM_ALIASES.get(text.upper())
    if not term_key and text.upper() in TERMS.get(lang, {}):
        term_key = text.upper()
    if term_key:
        lang_terms = TERMS.get(lang, TERMS['en'])
        explanation = lang_terms.get(term_key) or TERMS['en'].get(term_key, t(uid, 'term_not_found'))
        await update.message.reply_text(explanation, parse_mode="Markdown")
    else:
        await update.message.reply_text(t(uid, 'term_not_found'))

async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    await update.message.reply_text(t(uid, 'enter_symbol'), parse_mode="Markdown")
    return WAITING_SYMBOL

async def receive_symbol(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    symbol = update.message.text.strip().upper()
    context.user_data['symbol'] = symbol
    tfs = t(uid, 'timeframes')
    keyboard = [
        [InlineKeyboardButton(tfs["1m"], callback_data="1m"), InlineKeyboardButton(tfs["5m"], callback_data="5m"), InlineKeyboardButton(tfs["15m"], callback_data="15m")],
        [InlineKeyboardButton(tfs["1h"], callback_data="1h"), InlineKeyboardButton(tfs["4h"], callback_data="4h")],
        [InlineKeyboardButton(tfs["1d"], callback_data="1d"), InlineKeyboardButton(tfs["1w"], callback_data="1w")],
    ]
    await update.message.reply_text(f"✅ {symbol}USDT\n\n{t(uid, 'choose_tf')}", reply_markup=InlineKeyboardMarkup(keyboard))
    return WAITING_TIMEFRAME

async def receive_timeframe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    timeframe = query.data
    symbol = context.user_data.get('symbol', 'BTC')
    tfs = t(uid, 'timeframes')
    await query.edit_message_text(f"{t(uid, 'analyzing')} {symbol}USDT ...")
    try:
        df = analyzer.fetch_ohlcv(symbol, timeframe, limit=200)
        patterns = analyzer.detect_patterns(df)
        trend_label, trend_type = analyzer.determine_trend(df)
        fib_levels, _, _ = analyzer.calc_fibonacci(df)
        supports, resistances = analyzer.find_support_resistance(df)
        scores = analyzer.compute_signal(df, patterns, trend_type)
        chart_buf = generate_chart(df, symbol, timeframe, patterns, trend_label, trend_type, fib_levels, supports, resistances, scores)
        text_result = analyzer.analyze(symbol, timeframe)
        await query.message.reply_photo(photo=chart_buf, caption=f"📊 {symbol}USDT | {tfs.get(timeframe)}")
        await query.message.reply_text(text_result, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error: {e}")
        await query.message.reply_text(f"{t(uid, 'error')} {str(e)}")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    await update.message.reply_text(t(uid, 'cancel'))
    return ConversationHandler.END


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN not set!")

    app = ApplicationBuilder().token(token).build()

    analyze_conv = ConversationHandler(
        entry_points=[CommandHandler("analyze", analyze_command)],
        states={
            WAITING_SYMBOL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_symbol)],
            WAITING_TIMEFRAME: [CallbackQueryHandler(receive_timeframe, pattern="^(1m|5m|15m|1h|4h|1d|1w)$")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    journal_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(journal_callback, pattern="^j_")],
        states={
            J_SYMBOL: [MessageHandler(filters.TEXT & ~filters.COMMAND, j_symbol)],
            J_DIRECTION: [CallbackQueryHandler(j_direction, pattern="^jd_")],
            J_ENTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, j_entry)],
            J_SL: [MessageHandler(filters.TEXT & ~filters.COMMAND, j_sl)],
            J_TP: [MessageHandler(filters.TEXT & ~filters.COMMAND, j_tp)],
            J_SIZE: [MessageHandler(filters.TEXT & ~filters.COMMAND, j_size)],
            J_NOTE: [MessageHandler(filters.TEXT, j_note)],
            J_CLOSE_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, j_close_id)],
            J_CLOSE_EXIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, j_close_exit)],
            J_CLOSE_PNL: [MessageHandler(filters.TEXT & ~filters.COMMAND, j_close_pnl)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("lang", lang_command))
    app.add_handler(CommandHandler("terms", terms_command))
    app.add_handler(CommandHandler("journal", journal_command))
    app.add_handler(CallbackQueryHandler(set_lang, pattern="^lang_"))
    app.add_handler(analyze_conv)
    app.add_handler(journal_conv)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logger.info("Bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
