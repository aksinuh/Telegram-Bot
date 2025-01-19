import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from tracker import create_crypto_compare_client, get_crypto_price
from dotenv import load_dotenv

# .env faylını yüklə
load_dotenv()

# Binance API müştərisi
crypto_compare_client = create_crypto_compare_client(os.getenv("CRYPTOCOMPARE_API_KEY"))


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

# /shut down komandası: Hazırda izlənən valyutaları dayandır
async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'tracking' in context.user_data:
        context.user_data.pop('tracking')
        await update.message.reply_text("Bütün izlənən valyutalar dayandırıldı⛔.")
    else:
        await update.message.reply_text("Hal-hazırda heç bir valyuta izlənmir.❌😴")