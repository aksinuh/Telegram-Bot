
import os
import asyncio
import logging
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
from tracker import create_crypto_compare_client, get_crypto_price

# .env faylını yüklə
load_dotenv()

# Binance API müştərisi
crypto_compare_client = create_crypto_compare_client(os.getenv("CRYPTOCOMPARE_API_KEY"))

# Logging
logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)

ADMIN_ID = 1724281113  # Adminin Telegram ID-sini buraya yazın

user_states = {}

# Vəziyyətlər
STATE_THRESHOLD = "threshold"  # Qiymət təyini vəziyyəti
STATE_BROADCAST = "broadcast"  # Yayım vəziyyəti

# Faylları idarəetmə funksiyaları
def load_user_ids():
    if os.path.exists("user_ids.json"):
        with open("user_ids.json", "r") as f:
            return json.load(f)
    else:
        return []

def save_user_ids(user_ids):
    with open("user_ids.json", "w") as f:
        json.dump(user_ids, f)

def initialize_user_file():
    if not os.path.exists("user_ids.json"):
        with open("user_ids.json", "w") as f:
            json.dump([], f)

initialize_user_file()

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    # İstifadəçinin vəziyyətini broadcast vəziyyətinə gətir
    user_states[chat_id] = STATE_BROADCAST
    
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Bu əmri yalnız admin istifadə edə bilər❌.")
        return

    # Broadcast rejimini aktiv edirik
    await update.message.reply_text("İstifadçilərə göndərmək istədiyiniz mesajı daxil edin:")

# Broadcast mesajı işlədikdə bu funksiya aktiv olur
async def handle_broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    # Vəziyyəti yoxlayırıq
    if user_states.get(chat_id) == STATE_BROADCAST:
        message = update.message.text
        user_ids = load_user_ids()

        # Növbə ilə mesaj göndəririk
        if not user_ids:
            await update.message.reply_text("Heç bir istifadəçiyə mesaj göndərilmədi, çünki istifadəçi tapılmadı.")
            return

        for user_id in user_ids:
            try:
                await context.bot.send_message(user_id, message)
                logging.info(f"Mesaj {user_id} istifadəçisinə göndərildi.")
            except Exception as e:
                logging.error(f"Mesaj göndərərkən xəta baş verdi: {e}")

        await update.message.reply_text("Mesaj bütün istifadəçilərə göndərildi.✅")
        user_states[chat_id] = None
    else:
        await update.message.reply_text("Əvvəlcə /broadcast komandasını istifadə edin.")

# /start komandasını idarə edən funksiya
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    # İstifadəçinin vəziyyətini threshold vəziyyətinə gətir
    user_states[chat_id] = STATE_THRESHOLD
    
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
    chat_id = update.effective_chat.id

    # Vəziyyəti yoxlayırıq
    if user_states.get(chat_id) == STATE_THRESHOLD:
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
        user_states[chat_id] = None

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
        
async def current(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("BTCUSDT", callback_data="current_BTCUSDT"),
         InlineKeyboardButton("ETHUSDT", callback_data="current_ETHUSDT")],
        [InlineKeyboardButton("BNBUSDT", callback_data="current_BNBUSDT"),
         InlineKeyboardButton("XRPUSDT", callback_data="current_XRPUSDT")],
        [InlineKeyboardButton("ADAUSDT", callback_data="current_ADAUSDT"),
         InlineKeyboardButton("DOGEUSDT", callback_data="current_DOGEUSDT")],
        [InlineKeyboardButton("SOLUSDT", callback_data="current_SOLUSDT"),
         InlineKeyboardButton("XLMUSDT", callback_data="current_XLMUSDT")],
        [InlineKeyboardButton("PEPEUSDT", callback_data="current_PEPEUSDT"),
         InlineKeyboardButton("PENGUUSDT", callback_data="current_PENGUUSDT")],
        [InlineKeyboardButton("VANAUSDT", callback_data="current_VANAUSDT"),
         InlineKeyboardButton("MOVEUSDT", callback_data="current_MOVEUSDT")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Hansı kriptovalyutanın qiymətini görmək istəyirsiniz?👁️", reply_markup=reply_markup)
       
# Seçilmiş valyutanın hazırkı qiymətini göstər
async def show_current_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    symbol = query.data.split("_")[1]
    current_price = get_crypto_price(crypto_compare_client, symbol)

    # Qiymət formatlama
    formatted_price = f"{current_price:.8f}".rstrip('0').rstrip('.')
    
    await query.message.reply_text(f"{symbol} üçün hazırkı qiymət: {formatted_price}$💸")
       
        
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Mesajın yuxarısında məlumat verilir.
    await update.message.reply_text(
        "Kriptovalyutaları izləmək üçün təkmilləşdirilmişəm.🕵️‍♂️📊\n\n"
        "Aşağıdakı komandalarla məni idarə edə bilərsiz:🤖\n\n"
        "/start - Botu başlat✅\n"
        "/list - Hazırda izlənən kriptovalyutaların siyahısını görmək🗒️\n"
        "/current - Hazırkı qiymətləri görmək💸\n"
        "/stop - Hazırda izlənən valyutaları dayandır⛔\n"
        "/help - Komandalar haqqında məlumat📋"
    )

async def check_price(context: ContextTypes.DEFAULT_TYPE):
    job_data = context.job.data
    chat_id = job_data.get('chat_id')
    symbol = job_data.get('symbol')
    threshold = float(job_data.get('threshold'))
    direction = job_data.get('direction')

    current_price = get_crypto_price(crypto_compare_client, symbol)
    formated_price = f"{current_price:.8f}".rstrip('0').rstrip('.')
    
    # Qiymət həddinə çatdıqda xəbərdarlıq göndərilir və sorğu dayandırılır
    if (direction == "yuxari" and float(current_price) >= threshold) or (direction == "asagi" and float(current_price) <= threshold):
        await context.bot.send_message(chat_id, text=f"{symbol} qiyməti {str(formated_price)}$ səviyyəsinə çatdı!📈🕵️‍♂️")

        # İzləməni dayandırmaq üçün izləmə məlumatını silirik
        if 'tracking' in context.job.data:
            del context.user_data['tracking'][symbol]

        # İş dayandırılır
        context.job.schedule_removal()

# /shut down komandası: Hazırda izlənən valyutaları dayandır
async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'tracking' in context.user_data:
        context.user_data.pop('tracking')
        await update.message.reply_text("Bütün izlənən valyutalar dayandırıldı⛔.")
    else:
        await update.message.reply_text("Hal-hazırda heç bir valyuta izlənmir.❌😴")

def main():
    application = Application.builder() \
        .token(os.getenv("TELEGRAM_BOT_TOKEN")) \
        .arbitrary_callback_data(True) \
        .post_init(lambda app: app.job_queue.start()) \
        .build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(show_current_price, pattern="^current_"))
    application.add_handler(CallbackQueryHandler(track_price, pattern="^(BTCUSDT|ETHUSDT|BNBUSDT|XRPUSDT|ADAUSDT|DOGEUSDT|SOLUSDT|PEPEUSDT|PENGUUSDT|VANAUSDT|MOVEUSDT|XLMUSDT)$"))
    application.add_handler(CallbackQueryHandler(direction_choice, pattern="^(yuxari|asagi)$"))
    application.add_handler(CallbackQueryHandler(handle_restart, pattern="^(start_again|end_tracking)$"))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("list", list_command))
    application.add_handler(CommandHandler("current", current))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, set_threshold))  # Qiymət hədəfi təyini
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_broadcast_message))  # Broadcast mesajları
    application.add_handler(CommandHandler("stop", stop_command))
    application.run_polling()


if __name__ == "__main__":
    main()


