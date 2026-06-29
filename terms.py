TERMS = {
    'fa': {
        'RSI': "📊 *RSI (شاخص قدرت نسبی)*\nبین 0 تا 100 است.\n• بالای 70: اشباع خرید (احتمال ریزش)\n• زیر 30: اشباع فروش (احتمال رشد)\n• بین 30-70: منطقه خنثی",
        'MACD': "📊 *MACD*\nتفاوت دو میانگین متحرک EMA12 و EMA26.\n• MACD بالای Signal: سیگنال خرید\n• MACD زیر Signal: سیگنال فروش\n• هیستوگرام مثبت: مومنتوم صعودی",
        'BOLLINGER': "📊 *باند بولینگر*\nسه خط: بالا، میانی، پایین.\n• قیمت بالای باند بالایی: اشباع خرید\n• قیمت زیر باند پایینی: اشباع فروش\n• باند باریک: نوسان کم، انفجار در راه است",
        'FIBONACCI': "📊 *فیبوناچی*\nسطوح حمایت و مقاومت:\n• 23.6% و 38.2%: اصلاح ضعیف\n• 50% و 61.8%: اصلاح معمول\n• 78.6%: اصلاح قوی\n• 161.8%: هدف امتداد",
        'SUPPORT': "📊 *حمایت (Support)*\nسطحی که قیمت معمولاً از آن برمیگردد.\n• هرچه بیشتر تست شده، قوی‌تر است\n• شکست حمایت = سیگنال نزولی",
        'RESISTANCE': "📊 *مقاومت (Resistance)*\nسطحی که قیمت در برابرش متوقف میشود.\n• هرچه بیشتر تست شده، قوی‌تر است\n• شکست مقاومت = سیگنال صعودی",
        'LONG': "📊 *لانگ (Long)*\nخرید با انتظار رشد قیمت.\n• سود: وقتی قیمت بالا میرود\n• ضرر: وقتی قیمت پایین میآید\n• مثال: BTC را در 60k میخری، در 70k میفروشی",
        'SHORT': "📊 *شورت (Short)*\nفروش با انتظار ریزش قیمت.\n• سود: وقتی قیمت پایین میرود\n• ضرر: وقتی قیمت بالا میرود\n• نیاز به بازار فیوچرز دارد",
        'SL': "📊 *حد ضرر (Stop Loss)*\nقیمتی که در آن از معامله خارج میشوید تا ضرر بیشتر نکنید.\n• باید قبل از ورود تعیین شود\n• حداکثر 1-2% از سرمایه ریسک کنید",
        'TP': "📊 *تارگت (Take Profit)*\nقیمتی که در آن سود میگیرید.\n• معمولاً چند تارگت تعیین میشود\n• TP1، TP2، TP3",
        'RR': "📊 *نسبت ریسک به ریوارد (R/R)*\nنسبت سود احتمالی به ضرر احتمالی.\n• R/R بالای 2 مناسب است\n• مثال: ریسک 100$، سود 200$ = R/R 2",
        'EMA': "📊 *میانگین متحرک نمایی (EMA)*\nخط میانگین قیمت با وزن بیشتر به داده‌های جدید.\n• EMA20: کوتاه‌مدت\n• EMA50: میان‌مدت\n• EMA200: بلندمدت\n• قیمت بالای EMA200: روند صعودی",
        'CANDLE': "📊 *کندل‌استیک*\nنمایش قیمت در یک بازه زمانی:\n• بدنه سبز: قیمت بسته شدن > باز شدن\n• بدنه قرمز: قیمت بسته شدن < باز شدن\n• سایه بالا: بالاترین قیمت\n• سایه پایین: پایین‌ترین قیمت",
        'VOLUME': "📊 *حجم معاملات (Volume)*\nتعداد کوین‌های معامله شده.\n• حجم بالا + رشد قیمت: روند قوی\n• حجم پایین + رشد قیمت: روند ضعیف\n• حجم ناگهانی: نشانه تغییر روند",
        'DOJI': "📊 *دوجی (Doji)*\nکندلی که باز و بسته شدن تقریباً یکسان است.\n• نشانه عدم قطعیت بازار\n• بعد از روند قوی = احتمال برگشت",
        'HAMMER': "📊 *هامر (Hammer)*\nکندل با سایه پایین بلند.\n• در کف قیمتی: سیگنال خرید\n• نشانه رد شدن قیمت‌های پایین",
        'ENGULFING': "📊 *انگالفینگ (Engulfing)*\nکندلی که کندل قبلی را کاملاً میپوشاند.\n• صعودی: سیگنال خرید قوی\n• نزولی: سیگنال فروش قوی",
        'ATR': "📊 *ATR (میانگین دامنه واقعی)*\nاندازه‌گیری نوسان بازار.\n• ATR بالا: بازار پرنوسان\n• ATR پایین: بازار آرام\n• برای تعیین حد ضرر استفاده میشود",
        'LIQUIDATION': "📊 *لیکوئید شدن (Liquidation)*\nبسته شدن اجباری پوزیشن در فیوچرز.\n• وقتی ضرر به مارجین میرسد\n• با لوریج بالا خطر لیکوئید بیشتر است",
        'LEVERAGE': "📊 *لوریج (Leverage)*\nمعامله با پول بیشتر از موجودی.\n• لوریج 10x: 100$ را با 1000$ معامله میکنید\n• سود و ضرر هر دو ضربدر میشوند\n• خطرناک برای مبتدیان",
        'WHALE': "📊 *وال (Whale)*\nسرمایه‌گذار با سرمایه بسیار بزرگ.\n• میتوانند بازار را تکان دهند\n• رصد حرکت وال‌ها مهم است",
        'PUMP': "📊 *پامپ (Pump)*\nرشد سریع و ناگهانی قیمت.\n• معمولاً با حجم بالا همراه است\n• پامپ مصنوعی: دستکاری بازار",
        'DUMP': "📊 *دامپ (Dump)*\nریزش سریع و ناگهانی قیمت.\n• معمولاً بعد از پامپ اتفاق میافتد\n• با ترس و فروش گسترده همراه است",
        'FOMO': "📊 *فومو (FOMO)*\nترس از جا ماندن (Fear Of Missing Out).\n• احساس عجله برای خرید در اوج\n• باعث تصمیمات اشتباه میشود",
        'FUD': "📊 *فاد (FUD)*\nترس، عدم اطمینان و تردید (Fear, Uncertainty, Doubt).\n• اخبار منفی برای کاهش قیمت\n• معمولاً ابزار دستکاری بازار است",
        'HODL': "📊 *هودل (HODL)*\nنگه داشتن ارز برای بلندمدت.\n• نقطه مقابل ترید کوتاه‌مدت\n• استراتژی مناسب برای بازارهای نزولی",
        'ALTCOIN': "📊 *آلت‌کوین (Altcoin)*\nهر ارز دیجیتال غیر از بیتکوین.\n• مثال: ETH، SOL، BNB\n• معمولاً نوسان بیشتری از BTC دارند",
        'DOMINANCE': "📊 *دامیننس بیتکوین*\nسهم بیتکوین از کل بازار.\n• دامیننس بالا: پول در BTC است\n• دامیننس پایین: پول به آلت‌کوین‌ها رفته",
    },
    'en': {
        'RSI': "📊 *RSI (Relative Strength Index)*\nRange: 0 to 100\n• Above 70: Overbought (potential drop)\n• Below 30: Oversold (potential rise)\n• 30-70: Neutral zone",
        'MACD': "📊 *MACD*\nDifference between EMA12 and EMA26.\n• MACD above Signal: Buy signal\n• MACD below Signal: Sell signal\n• Positive histogram: Bullish momentum",
        'BOLLINGER': "📊 *Bollinger Bands*\nThree lines: Upper, Middle, Lower.\n• Price above upper band: Overbought\n• Price below lower band: Oversold\n• Narrow bands: Low volatility, breakout incoming",
        'FIBONACCI': "📊 *Fibonacci Levels*\nSupport & Resistance levels:\n• 23.6% & 38.2%: Weak retracement\n• 50% & 61.8%: Normal retracement\n• 78.6%: Strong retracement\n• 161.8%: Extension target",
        'LONG': "📊 *Long Position*\nBuying expecting price to rise.\n• Profit: when price goes up\n• Loss: when price goes down",
        'SHORT': "📊 *Short Position*\nSelling expecting price to fall.\n• Profit: when price goes down\n• Loss: when price goes up\n• Requires futures market",
        'SL': "📊 *Stop Loss*\nPrice at which you exit to limit losses.\n• Always set before entering a trade\n• Risk max 1-2% of capital per trade",
        'TP': "📊 *Take Profit*\nPrice at which you collect profit.\n• Usually multiple targets: TP1, TP2, TP3",
        'RR': "📊 *Risk/Reward Ratio*\nRatio of potential profit to potential loss.\n• R/R above 2 is recommended\n• Example: Risk $100, Gain $200 = R/R 2",
        'EMA': "📊 *Exponential Moving Average (EMA)*\n• EMA20: Short-term trend\n• EMA50: Mid-term trend\n• EMA200: Long-term trend\n• Price above EMA200: Bullish trend",
        'LEVERAGE': "📊 *Leverage*\nTrading with more than your balance.\n• 10x leverage: trade $1000 with $100\n• Both profits and losses are multiplied\n• Very risky for beginners",
        'LIQUIDATION': "📊 *Liquidation*\nForced closing of a futures position.\n• Happens when losses reach your margin\n• Higher leverage = higher liquidation risk",
        'FOMO': "📊 *FOMO (Fear Of Missing Out)*\nRushing to buy at the peak.\n• Leads to poor trading decisions\n• Buy high, sell low pattern",
        'FUD': "📊 *FUD (Fear, Uncertainty, Doubt)*\nNegative news to push prices down.\n• Often used to manipulate markets",
        'HODL': "📊 *HODL*\nHolding crypto long-term.\n• Opposite of short-term trading\n• Good strategy during bear markets",
        'PUMP': "📊 *Pump*\nRapid price increase.\n• Usually with high volume\n• Artificial pump = market manipulation",
        'DUMP': "📊 *Dump*\nRapid price decrease.\n• Usually follows a pump\n• Accompanied by panic selling",
        'WHALE': "📊 *Whale*\nInvestor with very large capital.\n• Can move the market\n• Tracking whale movements is important",
        'VOLUME': "📊 *Volume*\nNumber of coins traded.\n• High volume + price rise: Strong trend\n• Low volume + price rise: Weak trend",
        'DOMINANCE': "📊 *Bitcoin Dominance*\nBitcoin's share of total market cap.\n• High dominance: Money is in BTC\n• Low dominance: Money flowing to altcoins",
    },
    'ru': {
        'RSI': "📊 *RSI (Индекс относительной силы)*\nДиапазон: 0-100\n• Выше 70: Перекуплен (возможное падение)\n• Ниже 30: Перепродан (возможный рост)\n• 30-70: Нейтральная зона",
        'MACD': "📊 *MACD*\nРазница между EMA12 и EMA26.\n• MACD выше сигнала: Сигнал покупки\n• MACD ниже сигнала: Сигнал продажи\n• Положительная гистограмма: Бычий импульс",
        'LONG': "📊 *Длинная позиция (Long)*\nПокупка в ожидании роста цены.\n• Прибыль: когда цена растёт\n• Убыток: когда цена падает",
        'SHORT': "📊 *Короткая позиция (Short)*\nПродажа в ожидании падения цены.\n• Прибыль: когда цена падает\n• Убыток: когда цена растёт\n• Требует фьючерсного рынка",
        'SL': "📊 *Стоп-лосс (Stop Loss)*\nЦена выхода для ограничения убытков.\n• Устанавливайте до входа в сделку\n• Риск не более 1-2% капитала",
        'TP': "📊 *Тейк-профит (Take Profit)*\nЦена фиксации прибыли.\n• Обычно несколько целей: TP1, TP2, TP3",
        'RR': "📊 *Соотношение риск/прибыль (R/R)*\n• Рекомендуется R/R выше 2\n• Пример: Риск $100, Прибыль $200 = R/R 2",
        'FIBONACCI': "📊 *Уровни Фибоначчи*\nУровни поддержки и сопротивления:\n• 23.6% и 38.2%: Слабая коррекция\n• 50% и 61.8%: Нормальная коррекция\n• 78.6%: Сильная коррекция\n• 161.8%: Цель расширения",
        'LEVERAGE': "📊 *Кредитное плечо (Leverage)*\nТорговля с суммой больше баланса.\n• Плечо 10x: торгуете $1000 имея $100\n• Прибыли и убытки умножаются\n• Очень рискованно для новичков",
        'FOMO': "📊 *FOMO (Страх упустить)*\nСпешка купить на пике.\n• Ведёт к неверным решениям",
        'FUD': "📊 *FUD (Страх, Неопределённость, Сомнение)*\nНегативные новости для снижения цены.\n• Часто используется для манипуляций",
        'HODL': "📊 *HODL*\nДолгосрочное удержание крипты.\n• Хорошая стратегия на медвежьем рынке",
        'PUMP': "📊 *Памп (Pump)*\nРезкий рост цены.\n• Обычно с высоким объёмом",
        'DUMP': "📊 *Дамп (Dump)*\nРезкое падение цены.\n• Обычно следует за пампом",
        'WHALE': "📊 *Кит (Whale)*\nИнвестор с очень большим капиталом.\n• Может двигать рынок",
        'VOLUME': "📊 *Объём торгов (Volume)*\n• Высокий объём + рост: Сильный тренд\n• Низкий объём + рост: Слабый тренд",
        'DOMINANCE': "📊 *Доминирование биткоина*\n• Высокое доминирование: деньги в BTC\n• Низкое доминирование: деньги в альткоины",
    }
}

TERM_ALIASES = {
    'rsi': 'RSI', 'ار اس ای': 'RSI', 'قدرت نسبی': 'RSI',
    'macd': 'MACD', 'مکدی': 'MACD',
    'bollinger': 'BOLLINGER', 'بولینگر': 'BOLLINGER', 'باند': 'BOLLINGER',
    'fibonacci': 'FIBONACCI', 'فیبوناچی': 'FIBONACCI', 'فیبو': 'FIBONACCI',
    'support': 'SUPPORT', 'حمایت': 'SUPPORT',
    'resistance': 'RESISTANCE', 'مقاومت': 'RESISTANCE',
    'long': 'LONG', 'لانگ': 'LONG', 'خرید': 'LONG',
    'short': 'SHORT', 'شورت': 'SHORT', 'فروش': 'SHORT',
    'stop loss': 'SL', 'sl': 'SL', 'حد ضرر': 'SL', 'استاپ': 'SL',
    'take profit': 'TP', 'tp': 'TP', 'تارگت': 'TP', 'هدف': 'TP',
    'rr': 'RR', 'ریسک': 'RR', 'ریوارد': 'RR',
    'ema': 'EMA', 'میانگین': 'EMA', 'moving average': 'EMA',
    'candle': 'CANDLE', 'کندل': 'CANDLE', 'شمع': 'CANDLE',
    'volume': 'VOLUME', 'حجم': 'VOLUME',
    'doji': 'DOJI', 'دوجی': 'DOJI',
    'hammer': 'HAMMER', 'هامر': 'HAMMER', 'چکش': 'HAMMER',
    'engulfing': 'ENGULFING', 'انگالفینگ': 'ENGULFING', 'پوشا': 'ENGULFING',
    'atr': 'ATR',
    'liquidation': 'LIQUIDATION', 'لیکوئید': 'LIQUIDATION', 'لیکویید': 'LIQUIDATION',
    'leverage': 'LEVERAGE', 'لوریج': 'LEVERAGE', 'اهرم': 'LEVERAGE',
    'whale': 'WHALE', 'وال': 'WHALE', 'نهنگ': 'WHALE',
    'pump': 'PUMP', 'پامپ': 'PUMP',
    'dump': 'DUMP', 'دامپ': 'DUMP',
    'fomo': 'FOMO', 'فومو': 'FOMO',
    'fud': 'FUD', 'فاد': 'FUD',
    'hodl': 'HODL', 'هودل': 'HODL',
    'altcoin': 'ALTCOIN', 'آلت': 'ALTCOIN', 'آلت‌کوین': 'ALTCOIN',
    'dominance': 'DOMINANCE', 'دامیننس': 'DOMINANCE', 'سلطه': 'DOMINANCE',
}

ALL_TERMS_FA = """📚 *اصطلاحات ترید - لیست کامل*

🔸 *اندیکاتورها:*
RSI | MACD | بولینگر | EMA | ATR

🔸 *پوزیشن:*
لانگ | شورت | حد ضرر | تارگت | R/R | لوریج | لیکوئید

🔸 *تحلیل تکنیکال:*
فیبوناچی | حمایت | مقاومت | حجم

🔸 *الگوهای کندل:*
کندل | دوجی | هامر | انگالفینگ

🔸 *بازار:*
وال | پامپ | دامپ | فومو | فاد | هودل | آلت‌کوین | دامیننس

برای توضیح هر اصطلاح، نام آن را بنویسید.
مثال: `RSI` یا `لانگ` یا `فیبوناچی`"""

ALL_TERMS_EN = """📚 *Trading Terms - Full List*

🔸 *Indicators:*
RSI | MACD | Bollinger | EMA | ATR

🔸 *Positions:*
Long | Short | Stop Loss | Take Profit | R/R | Leverage | Liquidation

🔸 *Technical Analysis:*
Fibonacci | Support | Resistance | Volume

🔸 *Candlestick Patterns:*
Candle | Doji | Hammer | Engulfing

🔸 *Market:*
Whale | Pump | Dump | FOMO | FUD | HODL | Altcoin | Dominance

Type any term to get its explanation.
Example: `RSI` or `Long` or `Fibonacci`"""

ALL_TERMS_RU = """📚 *Термины трейдинга - Полный список*

🔸 *Индикаторы:*
RSI | MACD | Bollinger | EMA | ATR

🔸 *Позиции:*
Long | Short | Stop Loss | Take Profit | R/R | Leverage | Liquidation

🔸 *Теханализ:*
Fibonacci | Support | Resistance | Volume

🔸 *Свечные паттерны:*
Candle | Doji | Hammer | Engulfing

🔸 *Рынок:*
Whale | Pump | Dump | FOMO | FUD | HODL | Altcoin | Dominance

Напишите любой термин для объяснения.
Пример: `RSI` или `Long` или `Fibonacci`"""

