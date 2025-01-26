import os
import logging
import json
from telegram import Update
from telegram.error import BadRequest, TimedOut

from sqlite import get_admin_ids, get_user_ids, add_message, delete_user,get_all_cryptos
from dotenv import load_dotenv
from telegram import Update
from handlers import start, track_price, direction_choice, handle_restart, set_threshold

from utils import (
    show_current_price, help_command, 
    list_command, current, stop_command
    )

from telegram.ext import (
    Application, CommandHandler,
    CallbackQueryHandler, MessageHandler,
    filters, ContextTypes, CallbackContext
)

# .env faylını yüklə
load_dotenv()

# Logging
logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)

 # Adminin Telegram ID-sini buraya yazın


broadcast_messages = []


async def show_current_price(update: Update, context: CallbackContext):
    try:
        query = update.callback_query
        # Callback query etibarlıdırsa cavab veririk
        if not query.is_answered:
            await query.answer(text="Məlumat yüklənir...", show_alert=True)
        else:
            print("Query artıq cavablandırılıb.")
    except BadRequest as e:
        print(f"Xəta: {e}. Callback query etibarsızdır.")
        await update.callback_query.answer(text="Üzr istəyirik, gecikmə yaşanır. Zəhmət olmasa bir az gözləyin.")
    except TimedOut as e:
        print(f"Xəta: {e}. Cavab verilmədi.")
        await update.callback_query.answer(text="İnternet bağlantınız zəifdir, zəhmət olmasa bir az gözləyin.")
    except Exception as e:
        print(f"Başqa bir xəta baş verdi: {e}")
        await update.callback_query.answer(text="Bilinməyən bir xəta baş verdi. Zəhmət olmasa sonra yenidən cəhd edin.")
        
# Broadcast mesajı işlədikdə bu funksiya aktiv olur
async def broadcast_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_ids = get_admin_ids()
    if update.effective_user.id not in admin_ids:
        await update.message.reply_text("Bu əmri yalnız admin istifadə edə bilər❌.")
        return
    
    if context.args:
        message = " ".join(context.args)  # Mesaj mətnini birləşdir
        broadcast_messages.append(message)  # Mesajı yadda saxla
        await update.message.reply_text(f"Mesaj göndərildi: {message}")
    else:
        await update.message.reply_text("Xahiş olunur mesaj mətnini daxil edin. Məsələn: /broadcast Bu bir test mesajıdır.")

# Adminlərə aid broadcast mesajların göndərilməsi (istəyə bağlı)
async def send_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = update.effective_user.id
    user_ids = get_user_ids() # İstifadəçilərin ID-lərini yüklə
    failed_users = [] # Xətaya səbəb olan istifadəçilər

    
    for message in broadcast_messages:
        for user_id in user_ids:
            try:
                await context.bot.send_message(chat_id=user_id, text=message)
                
                
            except Exception as e:
                 # Əgər istifadəçi botu bloklayıbsa, ID-ni qeyd et
                if "bot was blocked by the user" in str(e):
                    failed_users.append(user_id)
    
                logging.error(f"Mesaj göndərərkən xəta baş verdi: {e}")
                
        add_message(admin_id, message)
        await update.message.reply_text("Mesaj bütün istifadəçilərə göndərildi.✅")
        
    if failed_users:
        for chat_id in failed_users:
            delete_user(chat_id)
             
        await update.message.reply_text(f"Bəzi istifadəçilər botu bloklayıb və siyahıdan silindi: {len(failed_users)} nəfər.❌")
        
    broadcast_messages.clear()


def main():
    application = Application.builder() \
        .token(os.getenv("TELEGRAM_BOT_TOKEN")) \
        .arbitrary_callback_data(True) \
        .post_init(lambda app: app.job_queue.start()) \
        .build()

    # Verilənlər bazasından kripto valyutaların siyahısını çəkirik
    cryptocurrencies = get_all_cryptos()

    # Siyahıdan pattern yaratmaq
    pattern = f"^({'|'.join(cryptocurrencies)})$"

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("list", list_command))
    application.add_handler(CommandHandler("current", current))
    application.add_handler(CommandHandler("stop", stop_command))
    application.add_handler(CommandHandler("broadcast", broadcast_handler))  # /broadcast üçün handler
    application.add_handler(CommandHandler("send_broadcast", send_broadcast))
    application.add_handler(CallbackQueryHandler(track_price, pattern=pattern))
    application.add_handler(CallbackQueryHandler(show_current_price, pattern="^current_"))
    application.add_handler(CallbackQueryHandler(direction_choice, pattern="^(yuxarı|aşağı)$"))
    application.add_handler(CallbackQueryHandler(handle_restart, pattern="^(start_again|end_tracking)$"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, set_threshold)) # Qiymət hədəfi təyini
    application.add_handler(CallbackQueryHandler(show_current_price, pattern='your_callback_pattern'))
    application.run_polling()


if __name__ == "__main__":
    main()


