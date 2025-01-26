import os
import asyncio

from sqlite import (
    add_user, initialize_database,
    get_all_cryptos,add_to_watchlist,
    get_user_watchlist, delete_watchlist_entry,
    get_crypto_symbol_by_id
)
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from tracker import create_crypto_compare_client, get_crypto_price


crypto_compare_client = create_crypto_compare_client(os.getenv("CRYPTOCOMPARE_API_KEY"))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.effective_user.id
    name = update.effective_user.username

    # İstifadəçini bazaya əlavə edin
    add_user(chat_id, name)

    cryptos = get_all_cryptos()
    
    # Dinamik olaraq düymələr yarat
    keyboard = []
    for i in range(0, len(cryptos), 2):  # Hər sətirdə 2 düymə
        row = [InlineKeyboardButton(cryptos[i], callback_data=cryptos[i])]
        if i + 1 < len(cryptos):  # İkinci düymənin mövcudluğunu yoxla
            row.append(InlineKeyboardButton(cryptos[i + 1], callback_data=cryptos[i + 1]))
        keyboard.append(row)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    effective_message = update.effective_message
    if effective_message:
        await effective_message.reply_text("Xoş gəlmisiniz!😊 Hansı kripto valyutanı izləmək istəyirsiniz?🕵️‍♂️",reply_markup=reply_markup)
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
                [InlineKeyboardButton("Yuxarı📈", callback_data="yuxarı"),
                 InlineKeyboardButton("Aşağı📉", callback_data="aşağı")]
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
        
        user_id = update.effective_user.id  # İstifadəçi ID-si
        crypto_id = symbol  # Kripto valyutasının ID-si
        target_price = threshold  # Təyin edilmiş qiymət
        # Məlumatları verilənlər bazasına əlavə edirik
        add_to_watchlist(user_id, crypto_id, target_price, direction)
        
        await asyncio.sleep(2)
        
                # İşin hər 10 saniyədə bir təkrarlanmasını təmin edirik
        context.job_queue.run_repeating(
            check_price, interval=10,  # 10 saniyə aralıqla sorğu göndəriləcək
            first=0,  # dərhal başlasın
            data={
                'user_id': update.effective_user.id,
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
        await asyncio.sleep(6)
        
async def check_price(context: ContextTypes.DEFAULT_TYPE):
    user_id = context.job.data.get("user_id")
    watchlist = get_user_watchlist(user_id)

    for entry in watchlist:
        watchlist_id, crypto_id, target_price, direction = entry
       
        current_price = get_crypto_price(crypto_compare_client, crypto_id)
        formated_price = f"{current_price:.8f}".rstrip('0').rstrip('.')
 
    # Qiymət həddinə çatdıqda xəbərdarlıq göndərilir və izləmə dayandırılır
    if (direction == "yuxarı" and float(current_price) >= target_price) or \
        (direction == "aşağı" and float(current_price) <= target_price):
            
        await context.bot.send_message(chat_id=user_id, text=f"{crypto_id} qiyməti {formated_price}$ səviyyəsinə çatdı!📈🕵️‍♂️")
        
        delete_watchlist_entry(watchlist_id)

        