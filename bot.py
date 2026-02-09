import logging, os, sqlite3, subprocess, time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler, CallbackQueryHandler

# --- الإعدادات النهائية ---
TOKEN = "8007978067:AAG6T3-b21_sbvlbUB1kj_rUF-LMrF0w2ME"
ADMIN_ID = 886470738
TIKTOK_USER = "Dar.799"
TIKTOK_LINK = "https://www.tiktok.com/@dar.799"
YOUTUBE_LINK = "https://www.youtube.com/@Darkness"

GLITCH_RULES = (
    "📜 **بروتوكول تحسين الجودة (The Glitch Protocol):**\n\n"
    "• 🎧 أضف الصوتيات في المونتاج (تجنب إضافتها عبر تيك توك).\n"
    "• 🎞️ الدقة 1080p بمعدل 60 FPS.\n"
    "• 📱 للأندرويد: ترميز h.264 وبتريت 20 Mbps.\n"
    "• 🍎 الرفع عبر الآيفون للأفضل دائماً."
)

logging.basicConfig(level=logging.INFO)

def init_db():
    conn = sqlite3.connect('users.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, attempts_left INTEGER DEFAULT 0, is_sub INTEGER DEFAULT 0, verified INTEGER DEFAULT 0)''')
    conn.commit(); conn.close()

def get_status(user_id):
    conn = sqlite3.connect('users.db')
    res = conn.execute("SELECT attempts_left, is_sub, verified FROM users WHERE user_id=?", (user_id,)).fetchone()
    if not res:
        conn.execute("INSERT INTO users VALUES (?, 0, 0, 0)", (user_id,))
        conn.commit(); res = (0, 0, 0)
    conn.close(); return res

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    _, _, verified = get_status(uid)
    if verified or uid == ADMIN_ID:
        await update.message.reply_text(f"🎯 **نظام انطلاقة المتطور.**\n\n{GLITCH_RULES}\n\n📥 أرسل الفيديو كـ **Document**.")
    else:
        keyboard = [[InlineKeyboardButton("1️⃣ تيك توك", url=TIKTOK_LINK), InlineKeyboardButton("2️⃣ يوتيوب", url=YOUTUBE_LINK)],
                    [InlineKeyboardButton("✅ تفعيل النظام", callback_data='verify')]]
        await update.message.reply_text("⚠️ **التفعيل مطلوب:** تابع الحسابات ثم اضغط تفعيل للحصول على 3 محاولات:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer(); uid = query.from_user.id
    conn = sqlite3.connect('users.db')
    conn.execute("UPDATE users SET verified=1, attempts_left=3 WHERE user_id=?", (uid,))
    conn.commit(); conn.close()
    await query.edit_message_text("✨ **تم التفعيل!** لديك 3 محاولات مجانية.\n\nأرسل الفيديو كـ **Document** حصراً.")

async def process_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    attempts, is_sub, verified = get_status(uid)
    if not verified and uid != ADMIN_ID: return await start(update, context)
    if attempts <= 0 and is_sub == 0 and uid != ADMIN_ID:
        return await update.message.reply_text(f"💰 **انتهى الرصيد.** الفيديو: 10 ريال.\nالمطور: {TIKTOK_USER}")

    if 'video' not in update.message.document.mime_type:
        return await update.message.reply_text("❌ يرجى إرسال ملف فيديو فقط.")

    status_msg = await update.message.reply_text("⚡ **يتم الآن الاتصال بالخادم... جاري التحميل.**")
    in_p, out_p = f"in_{uid}.mp4", f"out_{uid}.mp4"
    try:
        file = await update.message.document.get_file()
        await file.download_to_drive(in_p)
        await status_msg.edit_text("⚙️ **جاري تطبيق خوارزمية الجودة (itsscale 2)...**")
        # تنفيذ أمر FFmpeg الخاص بك
        subprocess.run(['ffmpeg', '-y', '-itsscale', '2', '-i', in_p, '-c', 'copy', out_p], check=True)
        await status_msg.edit_text("📤 **اكتملت المعالجة. جاري الرفع الآن...**")
        with open(out_p, 'rb') as f:
            await update.message.reply_document(document=f, caption=f"✅ **اكتملت المهمة بنجاح.**\n👤 المطور: {TIKTOK_USER}")
        if is_sub == 0 and uid != ADMIN_ID:
            conn = sqlite3.connect('users.db')
            conn.execute("UPDATE users SET attempts_left = attempts_left - 1 WHERE user_id=?", (uid,))
            conn.commit(); conn.close()
    finally:
        if os.path.exists(in_p): os.remove(in_p)
        if os.path.exists(out_p): os.remove(out_p)
        try: await context.bot.delete_message(chat_id=uid, message_id=status_msg.message_id)
        except: pass

if __name__ == '__main__':
    init_db()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.Document.ALL, process_document))
    app.add_handler(MessageHandler(filters.VIDEO, lambda u,c: u.message.reply_text("⚠️ أرسل الفيديو كـ **Document** (ملف) للحفاظ على الجودة.")))
    app.run_polling()
