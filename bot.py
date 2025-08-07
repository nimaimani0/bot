import sqlite3
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from datetime import datetime, timedelta
import threading
import time
import pytz

# تنظیمات اولیه
TOKEN = "7958571747:AAGQvtnz8BgKIaPM1o0WQeoolJAsXdzEHwM"
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

init_db()

# تابع شروع ربات
def start(update: Update, context: CallbackContext):
    user = update.effective_user
    update.message.reply_text(
        f"سلام {user.first_name}! 👋\n\n"
        "من ربات یادآوری هستم. برای تنظیم یادآوری جدید از دستور زیر استفاده کن:\n"
        "/set <زمان> <متن یادآوری>\n\n"
        "مثال:\n/set 10m خرید نان\n\n"
        "پشتیبانی از واحدهای زمانی:\n"
        "• m: دقیقه (مثال: 15m)\n"
        "• h: ساعت (مثال: 2h)\n"
        "• d: روز (مثال: 1d)"
    )

# تابع تنظیم یادآوری
def set_reminder(update: Update, context: CallbackContext):
    args = context.args
    if len(args) < 2:
        update.message.reply_text(
            "⚠️ لطفا زمان و متن یادآوری را وارد کنید!\n\n"
            "فرمت صحیح:\n/set <زمان> <متن یادآوری>\n\n"
            "مثال:\n/set 10m خرید نان"
        )
        return

    time_input = args[0].lower()
    reminder_text = " ".join(args[1:])
    timezone = pytz.timezone('Asia/Tehran')  # استفاده از زمان ایران

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

        reminder_time = datetime.now(timezone) + timedelta(seconds=seconds)

        # ذخیره در دیتابیس
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO reminders (user_id, reminder_text, reminder_time) VALUES (?, ?, ?)",
            (update.effective_user.id, reminder_text, reminder_time.isoformat())
        )
        conn.commit()
        conn.close()

        # نمایش زمان به صورت محلی
        local_time = reminder_time.strftime('%Y-%m-%d %H:%M:%S')
        
        update.message.reply_text(
            f"✅ یادآوری تنظیم شد!\n"
            f"📝 متن: {reminder_text}\n"
            f"⏰ زمان: {local_time}"
        )

    except ValueError:
        update.message.reply_text(
            "⛔ زمان نامعتبر! لطفا یکی از فرمت‌های زیر را استفاده کنید:\n\n"
            "• 15m (15 دقیقه)\n"
            "• 2h (2 ساعت)\n"
            "• 1d (1 روز)\n\n"
            "مثال صحیح:\n/set 10m خرید نان"
        )

# تابع چک کردن یادآوری‌ها
def check_reminders(bot):
    timezone = pytz.timezone('Asia/Tehran')  # استفاده از زمان ایران
    while True:
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            now = datetime.now(timezone).isoformat()
            cursor.execute("SELECT * FROM reminders WHERE reminder_time <= ?", (now,))
            reminders = cursor.fetchall()

            for reminder in reminders:
                user_id, reminder_text = reminder[1], reminder[2]
                try:
                    bot.send_message(user_id, f"⏰ یادآوری:\n{reminder_text}")
                    cursor.execute("DELETE FROM reminders WHERE id = ?", (reminder[0],))
                except Exception as e:
                    print(f"Error sending reminder: {e}")
                    # حذف یادآوری اگر کاربر ربات را بلاک کرده باشد
                    cursor.execute("DELETE FROM reminders WHERE id = ?", (reminder[0],))

            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
        
        time.sleep(10)  # هر ۱۰ ثانیه چک کن

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # دستورات ربات
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("set", set_reminder))

    # شروع ترد چک کردن یادآوری‌ها فقط یکبار
    if not hasattr(main, "reminder_thread_started"):
        threading.Thread(
            target=check_reminders, 
            args=(updater.bot,), 
            daemon=True
        ).start()
        main.reminder_thread_started = True

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()