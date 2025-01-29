import os
import json
from sqlite import get_all_cryptos, save_crypto_view, get_user_watchlist, get_user_watchlist_2, delete_user_watchlist,delete_all_user_watchlist
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from tracker import create_crypto_compare_client, get_crypto_price
from dotenv import load_dotenv

# .env faylını yüklə
load_dotenv()

# Binance API müştərisi
crypto_compare_client = create_crypto_compare_client(os.getenv("CRYPTOCOMPARE_API_KEY"))


async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id  # Telegram istifadəçi ID-sini əldə edirik
    # Verilənlər bazasından məlumatları alırıq
    tracking = get_user_watchlist(user_id)
    
    if not tracking:
        await update.message.reply_text("Hal-hazırda heç bir kriptovalyuta izlənmir.😴")
    else:
        msg = "Hazırda izlədiyiniz valyutalar🕵️‍♂️💸:\n\n"
        for row in tracking:
            watchlist_id, crypto_name, target_price, direction = row
            direction_text = 'Yuxarı📈' if direction == 'yuxarı' else 'Aşağı📉'
            msg += f"{crypto_name} - Səviyyə: {target_price}$, Yön: {direction_text}\n___________________________\n"
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
async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    watchlist = get_user_watchlist_2(user_id)

    if not watchlist:
        await update.message.reply_text("Hal-hazırda izlədiyiniz heç bir valyuta yoxdur.💱⛔")
        return

    # Düymələri 2 sütunlu düzülüşlə qur
    keyboard = [
        [InlineKeyboardButton(watchlist[i], callback_data=f"delete_{watchlist[i]}"),
         InlineKeyboardButton(watchlist[i + 1], callback_data=f"delete_{watchlist[i + 1]}")]
        for i in range(0, len(watchlist) - 1, 2)
    ]
    # Tək sayda valyuta varsa, sonuncu düyməni əlavə edin
    if len(watchlist) % 2 != 0:
        keyboard.append([InlineKeyboardButton(watchlist[-1], callback_data=f"delete_{watchlist[-1]}")])
    keyboard.append([InlineKeyboardButton("Hamısını Sil 🗑️", callback_data="delete_all")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("İzlədiyiniz valyutalar aşağıdakılardır. Silmək istədiyinizi seçin:🗑️", reply_markup=reply_markup)


async def handle_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = update.effective_user.id
    await query.message.delete()
    
    if data == "delete_all":    
        delete_all_user_watchlist(user_id)
        await query.message.reply_text("Bütün izləmələriniz silindi.🗑️")
        
    elif data.startswith("delete_"):
        crypto_id = data.replace("delete_", "")
        # Verilənlər bazasından valyutanı sil
        delete_user_watchlist(user_id, crypto_id)
        await query.message.reply_text(f"{crypto_id} izləmə siyahısından silindi.✔️")