import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
from datetime import datetime, timedelta
import threading
import time

# تنظیمات اولیه
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"  # توکن ربات را اینجا قرار بده
DB_NAME = "reminders.db"

# ایجاد دیتابیس SQLite
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            reminder_text TEXT,
            reminder_time TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()  # ایجاد دیتابیس در صورت عدم وجود

# تابع شروع ربات
def start(update: Update, context: CallbackContext):
    user = update.effective_user
    update.message.reply_text(f"سلام {user.first_name}! 👋\n\n"
                             "من ربات یادآوری هستم. می‌توانی با دستور /set یک یادآوری جدید تنظیم کنی.")

# تابع تنظیم یادآوری
def set_reminder(update: Update, context: CallbackContext):
    args = context.args
    if len(args) < 2:
        update.message.reply_text("⚠️ فرمت صحیح:\n/set <زمان> <متن یادآوری>\nمثال:\n/set 10m خرید نان")
        return

    time_input = args[0]
    reminder_text = " ".join(args[1:])

    try:
        # تبدیل زمان به ثانیه
        if time_input.endswith("m"):
            seconds = int(time_input[:-1]) * 60
        elif time_input.endswith("h"):
            seconds = int(time_input[:-1]) * 3600
        elif time_input.endswith("d"):
            seconds = int(time_input[:-1]) * 86400
        else:
            seconds = int(time_input)

        reminder_time = datetime.now() + timedelta(seconds=seconds)

        # ذخیره در دیتابیس
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO reminders (user_id, reminder_text, reminder_time) VALUES (?, ?, ?)",
            (update.effective_user.id, reminder_text, reminder_time.isoformat())
        )
        conn.commit()
        conn.close()

        update.message.reply_text(
            f"✅ یادآوری تنظیم شد!\n"
            f"📝 متن: {reminder_text}\n"
            f"⏰ زمان: {reminder_time.strftime('%Y-%m-%d %H:%M:%S')}"
        )

        # ایجاد ترد برای چک کردن یادآوری‌ها
        threading.Thread(target=check_reminders, args=(context.bot,)).start()

    except ValueError:
        update.message.reply_text("⛔ زمان نامعتبر! مثال صحیح:\n/set 10m خرید نان")

# تابع چک کردن یادآوری‌ها
def check_reminders(bot):
    while True:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute("SELECT * FROM reminders WHERE reminder_time <= ?", (now,))
        reminders = cursor.fetchall()

        for reminder in reminders:
            user_id, reminder_text = reminder[1], reminder[2]
            bot.send_message(user_id, f"⏰ یادآوری:\n{reminder_text}")
            cursor.execute("DELETE FROM reminders WHERE id = ?", (reminder[0],))

        conn.commit()
        conn.close()
        time.sleep(10)  # هر ۱۰ ثانیه چک کن

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # دستورات ربات
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("set", set_reminder))

    updater.start_polling()
    updater.idle()

if name == 'main':
    main()