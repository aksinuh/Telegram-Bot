import os
import logging
import json

from dotenv import load_dotenv
from telegram import Update
from handlers import start, track_price, direction_choice, handle_restart, set_threshold

from utils import (
    show_current_price, help_command, 
    list_command, current, stop_command,
    load_user_ids, save_user_ids
    )

from telegram.ext import (
    Application, CommandHandler,
    CallbackQueryHandler, MessageHandler,
    filters, ContextTypes,
)

# .env faylını yüklə
load_dotenv()

# Logging
logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)

ADMIN_ID = 1724281113  # Adminin Telegram ID-sini buraya yazın


broadcast_messages = []

def initialize_user_file():
    if not os.path.exists("user_ids.json"):
        with open("user_ids.json", "w") as f:
            json.dump([], f)

initialize_user_file()


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Bu əmri yalnız admin istifadə edə bilər❌.")
        return

    # Broadcast rejimini aktiv edirik
    await update.message.reply_text("İstifadəçilərə göndərmək istədiyiniz mesajı daxil edin:")
    

# Broadcast mesajı işlədikdə bu funksiya aktiv olur
async def broadcast_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
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
    user_ids = load_user_ids()  # İstifadəçilərin ID-lərini yüklə
    for message in broadcast_messages:
        for user_id in user_ids:
            try:
                await context.bot.send_message(chat_id=user_id, text=message)
            except Exception as e:
                logging.error(f"Mesaj göndərərkən xəta baş verdi: {e}")

        await update.message.reply_text("Mesaj bütün istifadəçilərə göndərildi.✅")
    broadcast_messages.clear()


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
    # application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("list", list_command))
    application.add_handler(CommandHandler("current", current))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, set_threshold))  # Qiymət hədəfi təyini
    application.add_handler(CommandHandler("broadcast", broadcast_handler))  # /broadcast üçün handler
    application.add_handler(CommandHandler("send_broadcast", send_broadcast))
    application.add_handler(CommandHandler("stop", stop_command))
    application.run_polling()


if __name__ == "__main__":
    main()


