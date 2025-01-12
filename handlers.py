import os
import asyncio
from utils import load_user_ids,save_user_ids
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes



from tracker import create_crypto_compare_client, get_crypto_price
crypto_compare_client = create_crypto_compare_client(os.getenv("CRYPTOCOMPARE_API_KEY"))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    user_ids = load_user_ids()

    # İstifadəçi ID-sini yalnız bir dəfə əlavə edirik
    if user_id not in user_ids:
        user_ids.append(user_id)
        save_user_ids(user_ids)  # Faylı avtomatik olaraq yeniləyirik

    # Botu başlatmaq üçün istifadəçinin qarşısında seçimlər
    keyboard = [
        [InlineKeyboardButton("BTCUSDT", callback_data="BTCUSDT"),
         InlineKeyboardButton("ETHUSDT", callback_data="ETHUSDT")],
        [InlineKeyboardButton("BNBUSDT", callback_data="BNBUSDT"),
         InlineKeyboardButton("XRPUSDT", callback_data="XRPUSDT")],
        [InlineKeyboardButton("ADAUSDT", callback_data="ADAUSDT"),
         InlineKeyboardButton("DOGEUSDT", callback_data="DOGEUSDT")],
        [InlineKeyboardButton("SOLUSDT", callback_data="SOLUSDT"),
         InlineKeyboardButton("XLMUSDT", callback_data="XLMUSDT")],
        [InlineKeyboardButton("PEPEUSDT", callback_data="PEPEUSDT"),
         InlineKeyboardButton("PENGUUSDT", callback_data="PENGUUSDT")],
        [InlineKeyboardButton("VANAUSDT", callback_data="VANAUSDT"),
         InlineKeyboardButton("MOVEUSDT", callback_data="MOVEUSDT")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    effective_message = update.effective_message
    if effective_message:
        await effective_message.reply_text(
            "Xoş gəlmisiniz!😊 Hansı kripto valyutanı izləmək istəyirsiniz?🕵️‍♂️",
            reply_markup=reply_markup
        )
        await asyncio.sleep(2)

# Qiymət izləmə funksiyası
async def track_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    symbol = query.data
    if 'tracking' not in context.user_data:
        context.user_data['tracking'] = {}

    context.user_data['current_symbol'] = symbol  # Mövcud valyutanı qeyd edin
    await query.message.reply_text(f"{symbol} izlənir.🕵️‍♂️ Bildirişlər üçün qiymət səviyyəsi daxil edin.🔔🔢")
    await asyncio.sleep(2)

async def set_threshold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'current_symbol' in context.user_data:
        context.user_data['tracking'] = {}

        symbol = context.user_data['current_symbol']
        try:
            threshold = float(update.message.text)
            context.user_data['tracking'][symbol] = {'threshold': threshold}
            keyboard = [
                [InlineKeyboardButton("Yuxarı📈", callback_data="yuxari"),
                 InlineKeyboardButton("Aşağı📉", callback_data="asagi")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                f"{symbol} üçün qiymət səviyyəsi {threshold}$ olaraq təyin edildi.👌✔️ "
                "Bildiriş üçün aşağıdakı seçimlərdən birini edin🔰:",
                reply_markup=reply_markup
            )
        except ValueError:
            await update.message.reply_text("Xahiş olunur düzgün mesajı daxil edin❌.")
    else:
        await update.message.reply_text("Əvvəlcə valyutanı seçin.💱⛔")

async def direction_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    direction = query.data
    symbol = context.user_data.get('current_symbol')

    if symbol and symbol in context.user_data['tracking']:
        context.user_data['tracking'][symbol]['direction'] = direction
        threshold = context.user_data['tracking'][symbol]['threshold']
        await query.message.reply_text(
            f"{symbol} üçün bildirişlər {threshold}$ səviyyəsinin '{'yuxarı📈' if direction == 'yuxari' else 'aşağı📉'}' keçməsi halında aktivdir.🔍📊"
        )
        await asyncio.sleep(2)
        
                # İşin hər 10 saniyədə bir təkrarlanmasını təmin edirik
        context.job_queue.run_repeating(
            check_price, interval=10,  # 10 saniyə aralıqla sorğu göndəriləcək
            first=0,  # dərhal başlasın
            data={
                'chat_id': update.effective_chat.id,
                'symbol': symbol,
                'threshold': threshold,
                'direction': direction
            },
            name=f"{update.effective_chat.id}_{symbol}"
        )

        # Yeni valyuta seçimi təklif edin
        keyboard = [
            [InlineKeyboardButton("Bəli ✅", callback_data="start_again"),
             InlineKeyboardButton("Xeyr ❎", callback_data="end_tracking")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("İzləmək istədiyiniz başqa bir valyuta var?🕵️‍♂️", reply_markup=reply_markup)
        await asyncio.sleep(1)
        
async def handle_restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "start_again":
        await start(update, context)
    else:
        await query.message.reply_text("İzləmə tamamlandı.✔️ Uğurlar!✨")
        await asyncio.sleep(5)
        
async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tracking = context.user_data.get('tracking', {})
    if not tracking:
        await update.message.reply_text("Hal-hazırda heç bir kriptovalyuta izlənmir.😴")
    else:
        msg = "Hazırda izlənən valyutalar🕵️‍♂️💸:\n"
        for symbol, data in tracking.items():
            threshold = data['threshold']
            direction = data.get('direction', '-')
            msg += f"{symbol} - Səviyyə: {threshold}$, Yön: {'Yuxarı📈' if direction == 'yuxari' else 'Aşağı📉'}\n"
        await update.message.reply_text(msg)
        
async def check_price(context: ContextTypes.DEFAULT_TYPE):
    job_data = context.job.data
    chat_id = job_data.get('chat_id')
    symbol = job_data.get('symbol')
    threshold = float(job_data.get('threshold'))
    direction = job_data.get('direction')

    current_price = get_crypto_price(crypto_compare_client, symbol)
    formated_price = f"{current_price:.8f}".rstrip('0').rstrip('.')

    # Qiymət həddinə çatdıqda xəbərdarlıq göndərilir və izləmə dayandırılır
    if (direction == "yuxari" and float(current_price) >= threshold) or (direction == "asagi" and float(current_price) <= threshold):
        await context.bot.send_message(chat_id, text=f"{symbol} qiyməti {formated_price}$ səviyyəsinə çatdı!📈🕵️‍♂️")
        context.job.schedule_removal()
        # İzləmə məlumatını silirik
        if 'tracking' in context.user_data:
            context.user_data['tracking'].pop(symbol, None)

        # Təkrar işi dayandırırıq
        