import os
import requests
import asyncio
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters
)

# Link Web App និង IDs
GOOGLE_WEB_APP_URL = os.environ.get("GOOGLE_WEB_APP_URL", "https://script.google.com/macros/s/AKfycbxyk03COogqCmuXafsBxeHLNJkNZhKhcPNj7giN0iSz7rtAk05n_5XeRR7QlLLrsFRj/exec")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8054966766:AAF0dn2k09D3Lrp_sF0CgAXoUWIopE0SOwE")
ADMIN_CHAT_ID = int(os.environ.get("ADMIN_CHAT_ID", "33459420"))

# ដំណាក់កាលសំណួរ
CAR_TYPE, PLATE_NUM, DRIVER_PHONE, ISSUE, REQUEST_DATE, STATUS = range(6)

# ផ្ទុកទិន្នន័យបណ្តោះអាសន្នសម្រាប់សំណើនីមួយៗ
pending_requests = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("🚗 **ការស្នើសុំជួសជុលរថយន្ត**\n\nសូមបញ្ចូល **ប្រភេទ និងម៉ាករថយន្ត** (ឧ. រថយន្ត Pick up Ford Wildtrack)៖")
    return CAR_TYPE

async def get_car_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['car_type'] = update.message.text
    await update.message.reply_text("សូមបញ្ចូល **ស្លាកលេខរថយន្ត** (ឧ. រដ្ឋ34-0209)៖")
    return PLATE_NUM

async def get_plate_num(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['plate_num'] = update.message.text
    await update.message.reply_text("សូមបញ្ចូល **លេខទូរស័ព្ទអ្នកបើកបរ** (ឧ. 012 345 678)៖")
    return DRIVER_PHONE

async def get_driver_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['driver_phone'] = update.message.text
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
    user_id = update.effective_user.id
    
    # ជូនដំណឹងទៅ User ឱ្យរង់ចាំ Admin ជ្រើសរើសយានដ្ឋាន
    await update.message.reply_text(
        "⏳ **បានបញ្ជូនសំណើជោគជ័យ!**\nសូមរង់ចាំ Admin ពិនិត្យ និងជ្រើសរើស «យានដ្ឋាន» ដើម្បីបញ្ចប់ការស្នើសុំ។",
        reply_markup=ReplyKeyboardRemove()
    )
    
    applicant_name = update.effective_user.first_name
    username = f"@{update.effective_user.username}" if update.effective_user.username else "គ្មាន"
    
    # រៀបចំសារផ្ញើជូន Admin
    admin_msg = (
        "🔔 **មានសំណើសុំជួសជុលរថយន្តថ្មី!**\n"
        "----------------------------------\n"
        f"👤 **អ្នកស្នើសុំ:** {applicant_name} ({username})\n"
        f"🚗 **ម៉ាករថយន្ត:** {u['car_type']}\n"
        f"🔢 **ស្លាកលេខ:** {u['plate_num']}\n"
        f"📞 **លេខទូរស័ព្ទ:** {u['driver_phone']}\n"
        f"🛠️ **កំហូច:** {u['issue']}\n"
        f"📅 **កាលបរិច្ឆេទស្នើសុំ:** {u['request_date']}\n"
        f"📝 **ស្ថានភាពលិខិត:** {u['status']}\n\n"
        "👉 **សូម Admin វាយបញ្ចូល «ឈ្មោះយានដ្ឋាន» ឆ្លើយតបមកវិញដើម្បីបញ្ចប់ការស្នើសុំ និង Record ចូល Google Sheet៖**"
    )
    
    # រក្សាទុកទិន្នន័យបណ្តោះអាសន្ន រង់ចាំ Admin បញ្ចូល Garage
    pending_requests[ADMIN_CHAT_ID] = {
        "user_id": user_id,
        "data": {
            "car_type": u['car_type'],
            "plate_num": u['plate_num'],
            "driver_phone": u['driver_phone'],
            "issue": u['issue'],
            "request_date": u['request_date'],
            "status": u['status']
        }
    }
    
    # ផ្ញើសារ Alert ទៅកាន់ Admin
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_msg)
    return ConversationHandler.END

# មុខងារសម្រាប់ Admin វាយបញ្ចូលឈ្មោះយានដ្ឋាន
async def handle_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    # ពិនិត្យថាជា Admin និងមានសំណើកំពុងរង់ចាំឬទេ
    if chat_id == ADMIN_CHAT_ID and chat_id in pending_requests:
        garage_name = update.message.text
        req_info = pending_requests.pop(chat_id)
        
        payload = req_info["data"]
        payload["garage"] = garage_name
        
        try:
            # បញ្ជូនទិន្នន័យទាំងអស់ចូល Google Sheet
            response = requests.post(GOOGLE_WEB_APP_URL, json=payload)
            if response.status_code == 200:
                # ជូនដំណឹងទៅ Admin
                await update.message.reply_text(
                    f"✅ **បានកត់ត្រា «{garage_name}» ចូល Google Sheet និងបញ្ចប់ការស្នើសុំរួចរាល់!**"
                )
                
                # ជូនដំណឹងទៅ User វិញ
                user_msg = (
                    "🎉 **សំណើជួសជុលរថយន្តរបស់អ្នកត្រូវបានអនុម័ត!**\n"
                    "----------------------------------\n"
                    f"🏢 **យានដ្ឋានចាត់តាំង:** {garage_name}\n"
                    f"🚗 **ម៉ាករថយន្ត:** {payload['car_type']} ({payload['plate_num']})\n\n"
                    "អរគុណ!"
                )
                await context.bot.send_message(chat_id=req_info["user_id"], text=user_msg)
            else:
                await update.message.reply_text("❌ មានបញ្ហាក្នុងការរក្សាទុកទិន្នន័យទៅ Google Sheet។")
        except Exception as e:
            await update.message.reply_text(f"❌ បរាជ័យ៖ {e}")

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
            DRIVER_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_driver_phone)],
            ISSUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_issue)],
            REQUEST_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_request_date)],
            STATUS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_status)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    app.add_handler(conv_handler)
    # បន្ថែម Handler សម្រាប់ Admin ឆ្លើយតបឈ្មោះយានដ្ឋាន
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_reply))
    
    print("Bot កំពុងដំណើរការ...")
    app.run_polling()

if __name__ == '__main__':
    main()
