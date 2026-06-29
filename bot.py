import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler, filters, ContextTypes
)
from analyzer import CryptoAnalyzer
from terms import TERMS, TERM_ALIASES, ALL_TERMS_FA, ALL_TERMS_EN, ALL_TERMS_RU

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

WAITING_SYMBOL, WAITING_TIMEFRAME = range(2)

TEXTS = {
    'fa': {
        'welcome': "👋 *سلام! به ربات تحلیل کریپتو خوش آمدید*\n\nتحلیل لانگ 📈 و شورت 📉 بر اساس:\n• الگوهای کندل‌استیک\n• سطوح فیبوناچی\n• RSI, MACD, Bollinger\n\n/analyze - شروع تحلیل\n/terms - اصطلاحات ترید\n/lang - تغییر زبان",
        'enter_symbol': "🪙 نام ارز را وارد کنید:\nمثال: `BTC`, `ETH`, `SOL`",
        'choose_tf': "تایم‌فریم را انتخاب کنید:",
        'analyzing': "⏳ در حال تحلیل",
        'error': "❌ خطا:",
        'cancel': "❌ لغو شد.",
        'help': "/analyze - شروع تحلیل\n/terms - اصطلاحات ترید\n/lang - تغییر زبان",
        'choose_lang': "🌐 زبان را انتخاب کنید:",
        'lang_set': "✅ زبان فارسی انتخاب شد.",
        'term_not_found': "❓ اصطلاح پیدا نشد.\n\n/terms را بزنید تا لیست کامل ببینید.",
        'timeframes': {"1m": "1 دقیقه", "5m": "5 دقیقه", "15m": "15 دقیقه", "1h": "1 ساعت", "4h": "4 ساعت", "1d": "روزانه", "1w": "هفتگی"},
    },
    'en': {
        'welcome': "👋 *Welcome to Crypto Analysis Bot!*\n\nLong 📈 & Short 📉 analysis based on:\n• Candlestick Patterns\n• Fibonacci Levels\n• RSI, MACD, Bollinger\n\n/analyze - Start analysis\n/terms - Trading terms\n/lang - Change language",
        'enter_symbol': "🪙 Enter coin symbol:\nExample: `BTC`, `ETH`, `SOL`",
        'choose_tf': "Select timeframe:",
        'analyzing': "⏳ Analyzing",
        'error': "❌ Error:",
        'cancel': "❌ Cancelled.",
        'help': "/analyze - Start analysis\n/terms - Trading terms\n/lang - Change language",
        'choose_lang': "🌐 Choose your language:",
        'lang_set': "✅ English selected.",
        'term_not_found': "❓ Term not found.\n\nUse /terms to see the full list.",
        'timeframes': {"1m": "1 Min", "5m": "5 Min", "15m": "15 Min", "1h": "1 Hour", "4h": "4 Hour", "1d": "Daily", "1w": "Weekly"},
    },
    'ru': {
        'welcome': "👋 *Добро пожаловать в бот анализа крипто!*\n\nАнализ Long 📈 и Short 📉 на основе:\n• Паттерны свечей\n• Уровни Фибоначчи\n• RSI, MACD, Bollinger\n\n/analyze - Начать анализ\n/terms - Термины трейдинга\n/lang - Сменить язык",
        'enter_symbol': "🪙 Введите символ монеты:\nПример: `BTC`, `ETH`, `SOL`",
        'choose_tf': "Выберите таймфрейм:",
        'analyzing': "⏳ Анализирую",
        'error': "❌ Ошибка:",
        'cancel': "❌ Отменено.",
        'help': "/analyze - Начать анализ\n/terms - Термины трейдинга\n/lang - Сменить язык",
        'choose_lang': "🌐 Выберите язык:",
        'lang_set': "✅ Русский выбран.",
        'term_not_found': "❓ Термин не найден.\n\nИспользуйте /terms для полного списка.",
        'timeframes': {"1m": "1 Мин", "5m": "5 Мин", "15m": "15 Мин", "1h": "1 Час", "4h": "4 Часа", "1d": "День", "1w": "Неделя"},
    }
}

analyzer = CryptoAnalyzer()
user_langs = {}


def get_lang(uid): return user_langs.get(uid, 'fa')
def t(uid, key): return TEXTS[get_lang(uid)][key]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    await update.message.reply_text(t(uid, 'welcome'), parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    await update.message.reply_text(t(uid, 'help'))


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
    if lang == 'fa':
        msg = ALL_TERMS_FA
    elif lang == 'en':
        msg = ALL_TERMS_EN
    else:
        msg = ALL_TERMS_RU
    await update.message.reply_text(msg, parse_mode="Markdown")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = get_lang(uid)
    text = update.message.text.strip().lower()

    term_key = TERM_ALIASES.get(text)
    if not term_key:
        term_key = TERM_ALIASES.get(text.upper())
    if not term_key and text.upper() in TERMS.get(lang, {}):
        term_key = text.upper()

    if term_key and term_key in TERMS.get(lang, TERMS['en']):
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
    await update.message.reply_text(
        f"✅ {symbol}USDT\n\n{t(uid, 'choose_tf')}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return WAITING_TIMEFRAME


async def receive_timeframe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    timeframe = query.data
    symbol = context.user_data.get('symbol', 'BTC')
    tfs = t(uid, 'timeframes')
    await query.edit_message_text(f"{t(uid, 'analyzing')} {symbol}USDT - {tfs.get(timeframe)} ...")
    try:
        result = analyzer.analyze(symbol, timeframe)
        await query.message.reply_text(result, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error: {e}")
        await query.message.reply_text(f"{t(uid, 'error')} {str(e)}")
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    await update.message.reply_text(t(uid, 'cancel'))
    return ConversationHandler.END


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN not set!")

    app = ApplicationBuilder().token(token).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("analyze", analyze_command)],
        states={
            WAITING_SYMBOL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_symbol)],
            WAITING_TIMEFRAME: [CallbackQueryHandler(receive_timeframe, pattern="^(1m|5m|15m|1h|4h|1d|1w)$")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("lang", lang_command))
    app.add_handler(CommandHandler("terms", terms_command))
    app.add_handler(CallbackQueryHandler(set_lang, pattern="^lang_"))
    app.add_handler(conv)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logger.info("Bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
