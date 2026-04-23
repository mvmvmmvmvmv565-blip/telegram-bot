import telebot
from telebot import types
import sqlite3

API_TOKEN = '8604946145:AAFokZV9qOhH-qHigCiPCCpmNGD06ks_BoI'
bot = telebot.TeleBot(API_TOKEN)

# قاعدة بيانات بسيطة
conn = sqlite3.connect('data.db')
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS btns (user_id INTEGER, name TEXT, content TEXT)')
conn.commit()

user_state = {}

@bot.message_handler(commands=['start'])
def start(msg):
    uid = msg.from_user.id
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('➕ زر جديد', '📋 أزرارى')
    bot.send_message(uid, "مرحباً! اختر من القائمة:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == '➕ زر جديد')
def new_btn(msg):
    user_state[msg.from_user.id] = 'name'
    bot.send_message(msg.from_user.id, "أرسل اسم الزر:")

@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == 'name')
def get_name(msg):
    uid = msg.from_user.id
    user_state[uid] = {'name': msg.text, 'step': 'content'}
    bot.send_message(uid, f"الاسم: {msg.text}\nأرسل المحتوى:")

@bot.message_handler(func=lambda m: isinstance(user_state.get(m.from_user.id), dict) and user_state[m.from_user.id]['step'] == 'content')
def save_btn(msg):
    uid = msg.from_user.id
    data = user_state[uid]
    c.execute('INSERT INTO btns VALUES (?, ?, ?)', (uid, data['name'], msg.text))
    conn.commit()
    del user_state[uid]
    bot.send_message(uid, f"✅ تم حفظ الزر {data['name']}")

@bot.message_handler(func=lambda m: m.text == '📋 أزرارى')
def list_btns(msg):
    uid = msg.from_user.id
    c.execute('SELECT name FROM btns WHERE user_id=?', (uid,))
    btns = c.fetchall()
    if not btns:
        bot.send_message(uid, "لا توجد أزرار")
        return
    markup = types.InlineKeyboardMarkup()
    for b in btns:
        markup.add(types.InlineKeyboardButton(b[0], callback_data=b[0]))
    bot.send_message(uid, "أزرارك:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def show(call):
    c.execute('SELECT content FROM btns WHERE user_id=? AND name=?', (call.from_user.id, call.data))
    res = c.fetchone()
    if res:
        bot.send_message(call.message.chat.id, res[0])

print("Bot is running...")
bot.infinity_polling()
