import os
import json
from sqlite import get_all_cryptos, save_crypto_view
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
    cryptos = get_all_cryptos()
    
    # Dinamik olaraq düymələr yarat
    keyboard = []
    for i in range(0, len(cryptos), 2):  # Hər sətirdə 2 düymə
        row = [InlineKeyboardButton(cryptos[i], callback_data=f"current_{cryptos[i]}")]
        if i + 1 < len(cryptos):  # İkinci düymənin mövcudluğunu yoxla
            row.append(InlineKeyboardButton(cryptos[i + 1], callback_data=f"current_{cryptos[i + 1]}"))
        keyboard.append(row)
    
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
    
    user_id = query.from_user.id
    save_crypto_view(user_id, symbol, current_price)
    
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