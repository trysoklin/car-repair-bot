import os
import requests
import asyncio
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters
)

# យក Link Web App ពី Environment Variable (ឬដាក់ Link ផ្ទាល់ត្រង់នេះ)
GOOGLE_WEB_APP_URL = os.environ.get("https://script.google.com/macros/s/xxxx/exec", " 
https://script.google.com/macros/s/AKfycbxFb1ndQs3UL08TDp6sspXirQGk0fiVyYQeB7vWkvZTIuJbgz4itnlXK_NErngHWJkr/exec")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8054966766:AAF0dn2k09D3Lrp_sF0CgAXoUWIopE0SOwE")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID", "33459420")

CAR_TYPE, PLATE_NUM, ISSUE, REQUEST_DATE, STATUS = range(5)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("🚗 **ការស្នើសុំជួសជុលរថយន្ត**\n\nសូមបញ្ចូល **ប្រភេទ និងម៉ាករថយន្ត** (ឧ. រថយន្ត Pick up Ford Wildtrack)៖")
    return CAR_TYPE

async def get_car_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['car_type'] = update.message.text
    await update.message.reply_text("សូមបញ្ចូល **ស្លាកលេខរថយន្ត** (ឧ. រដ្ឋ34-0209)៖")
    return PLATE_NUM

async def get_plate_num(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['plate_num'] = update.message.text
    await update.message.reply_text("សូមរៀបរាប់ **កំហូចរបស់រថយន្ត** (ឧ. តម្រងប្រេងម៉ាស៊ីន)៖")
    return ISSUE

async def get_issue(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['issue'] = update.message.text
    await update.message.reply_text("សូមបញ្ចូល **កាលបរិច្ឆេទស្នើសុំ** (ឧ. 31-08-2026)៖")
    return REQUEST_DATE

async def get_request_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['request_date'] = update.message.text
    reply_keyboard = [['ស្នើសុំផ្លូវការ', 'មិនទាន់ស្នើសុំផ្លូវការ']]
    await update.message.reply_text(
        "សូមជ្រើសរើស **ស្ថានភាពលិខិតស្នើសុំជួសជុល**៖",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True),
    )
    return STATUS

async def get_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['status'] = update.message.text
    u = context.user_data
    
    payload = {
        "car_type": u['car_type'],
        "plate_num": u['plate_num'],
        "issue": u['issue'],
        "request_date": u['request_date'],
        "status": u['status']
    }
    
    try:
        response = requests.post(GOOGLE_WEB_APP_URL, json=payload)
        if response.status_code == 200:
            await update.message.reply_text(
                "✅ **បានបញ្ជូនសំណើ និងរក្សាទុកក្នុង Google Sheet រួចរាល់!**",
                reply_markup=ReplyKeyboardRemove()
            )
            
            applicant_name = update.effective_user.first_name
            username = f"@{update.effective_user.username}" if update.effective_user.username else "គ្មាន"
            
            admin_msg = (
                "🔔 **មានសំណើសុំជួសជុលរថយន្តថ្មី!**\n"
                "----------------------------------\n"
                f"👤 **អ្នកស្នើសុំ:** {applicant_name} ({username})\n"
                f"🚗 **ម៉ាករថយន្ត:** {u['car_type']}\n"
                f"🔢 **ស្លាកលេខ:** {u['plate_num']}\n"
                f"🛠️ **កំហូច:** {u['issue']}\n"
                f"📅 **កាលបរិច្ឆេទស្នើសុំ:** {u['request_date']}\n"
                f"📝 **ស្ថានភាពលិខិត:** {u['status']}\n\n"
                "⚠️ *សូម Admin ចូលទៅ Google Sheet ដើម្បីបំពេញ «យានដ្ឋាន» និង «កាលបរិច្ឆេទជួសជុល» បន្ថែម!*"
            )
            await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_msg)
            
        else:
            await update.message.reply_text("❌ មានបញ្ហាក្នុងការរក្សាទុកទិន្នន័យ។")
    except Exception as e:
        await update.message.reply_text(f"❌ បរាជ័យ៖ {e}")

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("បានបោះបង់ប្រតិបត្តិការ។", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start), CommandHandler('add', start)],
        states={
            CAR_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_car_type)],
            PLATE_NUM: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_plate_num)],
            ISSUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_issue)],
            REQUEST_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_request_date)],
            STATUS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_status)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    app.add_handler(conv_handler)
    print("Bot កំពុងដំណើរការ...")
    app.run_polling()

if __name__ == '__main__':
    main()
