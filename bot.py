import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler, filters, ContextTypes
)
from analyzer import CryptoAnalyzer

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# States
WAITING_SYMBOL, WAITING_TIMEFRAME = range(2)

TIMEFRAMES = {
    "1m": "1 دقیقه",
    "5m": "5 دقیقه",
    "15m": "15 دقیقه",
    "1h": "1 ساعت",
    "4h": "4 ساعت",
    "1d": "روزانه",
    "1w": "هفتگی",
}

analyzer = CryptoAnalyzer()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 *سلام! به ربات تحلیل کریپتو خوش آمدید*\n\n"
        "🔍 این ربات بر اساس:\n"
        "• الگوهای کندل‌استیک (Candlestick Patterns)\n"
        "• سطوح فیبوناچی (Fibonacci Levels)\n"
        "• اندیکاتورهای تکنیکال (RSI, MACD, Bollinger)\n\n"
        "تحلیل لانگ 📈 و شورت 📉 ارائه می‌دهد.\n\n"
        "برای شروع تحلیل دستور /analyze را بزنید.",
        parse_mode="Markdown"
    )


async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🪙 *نام ارز دیجیتال را وارد کنید:*\n\n"
        "مثال‌ها: `BTC`, `ETH`, `SOL`, `BNB`, `XRP`\n\n"
        "⚠️ فقط نماد ارز را بدون USDT وارد کنید.",
        parse_mode="Markdown"
    )
    return WAITING_SYMBOL


async def receive_symbol(update: Update, context: ContextTypes.DEFAULT_TYPE):
    symbol = update.message.text.strip().upper()
    context.user_data['symbol'] = symbol

    keyboard = [
        [
            InlineKeyboardButton("1 دقیقه", callback_data="1m"),
            InlineKeyboardButton("5 دقیقه", callback_data="5m"),
            InlineKeyboardButton("15 دقیقه", callback_data="15m"),
        ],
        [
            InlineKeyboardButton("1 ساعت", callback_data="1h"),
            InlineKeyboardButton("4 ساعت", callback_data="4h"),
        ],
        [
            InlineKeyboardButton("روزانه", callback_data="1d"),
            InlineKeyboardButton("هفتگی", callback_data="1w"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"✅ ارز انتخابی: *{symbol}USDT*\n\n⏱ *تایم‌فریم مورد نظر را انتخاب کنید:*",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return WAITING_TIMEFRAME


async def receive_timeframe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    timeframe = query.data
    symbol = context.user_data.get('symbol', 'BTC')
    tf_name = TIMEFRAMES.get(timeframe, timeframe)

    await query.edit_message_text(
        f"⏳ در حال تحلیل *{symbol}USDT* در تایم‌فریم *{tf_name}* ...\n\n"
        "لطفاً چند ثانیه صبر کنید 🔄",
        parse_mode="Markdown"
    )

    try:
        result = analyzer.analyze(symbol, timeframe)
        await query.message.reply_text(result, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        await query.message.reply_text(
            f"❌ خطا در تحلیل: {str(e)}\n\n"
            "لطفاً نماد ارز را بررسی کرده و دوباره امتحان کنید.",
            parse_mode="Markdown"
        )

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ عملیات لغو شد.")
    return ConversationHandler.END


async def quick_analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle quick analysis like /btc or /eth"""
    text = update.message.text.lstrip('/').upper()
    parts = text.split()
    symbol = parts[0]
    timeframe = parts[1] if len(parts) > 1 else "1h"

    if timeframe not in TIMEFRAMES:
        timeframe = "1h"

    await update.message.reply_text(
        f"⏳ در حال تحلیل *{symbol}USDT* در تایم‌فریم *{TIMEFRAMES[timeframe]}* ...",
        parse_mode="Markdown"
    )

    try:
        result = analyzer.analyze(symbol, timeframe)
        await update.message.reply_text(result, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {str(e)}")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *راهنمای استفاده:*\n\n"
        "🔹 `/analyze` - شروع تحلیل تعاملی\n"
        "🔹 `/btc 1h` - تحلیل سریع بیتکوین در 1 ساعته\n"
        "🔹 `/eth 4h` - تحلیل سریع اتریوم در 4 ساعته\n\n"
        "⏱ *تایم‌فریم‌های موجود:*\n"
        "`1m` `5m` `15m` `1h` `4h` `1d` `1w`\n\n"
        "📊 *اندیکاتورهای استفاده شده:*\n"
        "• الگوهای کندل‌استیک\n"
        "• سطوح فیبوناچی\n"
        "• RSI\n"
        "• MACD\n"
        "• باند بولینگر\n"
        "• میانگین متحرک (EMA 20/50/200)",
        parse_mode="Markdown"
    )


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set!")

    app = Application.builder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("analyze", analyze_command)],
        states={
            WAITING_SYMBOL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_symbol)],
            WAITING_TIMEFRAME: [CallbackQueryHandler(receive_timeframe)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(conv_handler)

    # Quick commands pattern: /BTC, /ETH, etc.
    app.add_handler(MessageHandler(
        filters.Regex(r'^/[A-Za-z]{2,10}(\s+(1m|5m|15m|1h|4h|1d|1w))?$'),
        quick_analyze
    ))

    logger.info("Bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
