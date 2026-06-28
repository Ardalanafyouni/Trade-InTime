import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler, filters, ContextTypes
)
from analyzer import CryptoAnalyzer

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

WAITING_SYMBOL, WAITING_TIMEFRAME = range(2)

TIMEFRAMES = {
    "1m": "1 دقیقه", "5m": "5 دقیقه", "15m": "15 دقیقه",
    "1h": "1 ساعت", "4h": "4 ساعت", "1d": "روزانه", "1w": "هفتگی",
}

analyzer = CryptoAnalyzer()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 *سلام! به ربات تحلیل کریپتو خوش آمدید*\n\n"
        "تحلیل لانگ 📈 و شورت 📉 بر اساس:\n"
        "• الگوهای کندل‌استیک\n"
        "• سطوح فیبوناچی\n"
        "• RSI, MACD, Bollinger\n\n"
        "دستور /analyze را بزنید.",
        parse_mode="Markdown"
    )


async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🪙 نام ارز را وارد کنید:\nمثال: `BTC`, `ETH`, `SOL`",
        parse_mode="Markdown"
    )
    return WAITING_SYMBOL


async def receive_symbol(update: Update, context: ContextTypes.DEFAULT_TYPE):
    symbol = update.message.text.strip().upper()
    context.user_data['symbol'] = symbol
    keyboard = [
        [InlineKeyboardButton("1m", callback_data="1m"), InlineKeyboardButton("5m", callback_data="5m"), InlineKeyboardButton("15m", callback_data="15m")],
        [InlineKeyboardButton("1h", callback_data="1h"), InlineKeyboardButton("4h", callback_data="4h")],
        [InlineKeyboardButton("1d روزانه", callback_data="1d"), InlineKeyboardButton("1w هفتگی", callback_data="1w")],
    ]
    await update.message.reply_text(
        f"✅ {symbol}USDT\n\nتایم‌فریم را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return WAITING_TIMEFRAME


async def receive_timeframe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    timeframe = query.data
    symbol = context.user_data.get('symbol', 'BTC')
    await query.edit_message_text(f"⏳ در حال تحلیل {symbol}USDT - {TIMEFRAMES.get(timeframe)} ...")
    try:
        result = analyzer.analyze(symbol, timeframe)
        await query.message.reply_text(result, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error: {e}")
        await query.message.reply_text(f"❌ خطا: {str(e)}")
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ لغو شد.")
    return ConversationHandler.END


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("/analyze - شروع تحلیل\n/help - راهنما")


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN not set!")

    app = ApplicationBuilder().token(token).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("analyze", analyze_command)],
        states={
            WAITING_SYMBOL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_symbol)],
            WAITING_TIMEFRAME: [CallbackQueryHandler(receive_timeframe)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(conv)

    logger.info("Bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
