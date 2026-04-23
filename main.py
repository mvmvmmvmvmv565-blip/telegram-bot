import telebot
from telebot import types
import sqlite3
import os

API_TOKEN = '8604946145:AAFokZV9qOhH-qHigCiPCCpmNGD06ks_BoI'
bot = telebot.TeleBot(API_TOKEN)

# قاعدة البيانات
conn = sqlite3.connect('bot_data.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)')
c.execute('CREATE TABLE IF NOT EXISTS buttons (user_id INTEGER, name TEXT, content TEXT)')
conn.commit()

user_states = {}

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('➕ إضافة زر', '📋 أزاري')
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    c.execute('INSERT OR IGNORE INTO users VALUES (?)', (uid,))
    conn.commit()
    bot.send_message(uid, "🎯 أهلاً بك! استخدم الأزرار بالأسفل.", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == '➕ إضافة زر')
def add_btn(message):
    user_states[message.from_user.id] = 'waiting_name'
    bot.send_message(message.from_user.id, "📝 أرسل اسم الزر:")

@bot.message_handler(func=lambda m: user_states.get(m.from_user.id) == 'waiting_name')
def get_name(message):
    uid = message.from_user.id
    user_states[uid] = {'name': message.text, 'step': 'waiting_content'}
    bot.send_message(uid, f"✅ الاسم: {message.text}\n📄 أرسل المحتوى:")

@bot.message_handler(func=lambda m: isinstance(user_states.get(m.from_user.id), dict) and user_states[m.from_user.id].get('step') == 'waiting_content')
def save_btn(message):
    uid = message.from_user.id
    data = user_states[uid]
    c.execute('INSERT INTO buttons VALUES (?, ?, ?)', (uid, data['name'], message.text))
    conn.commit()
    del user_states[uid]
    bot.send_message(uid, f"🎉 تم حفظ الزر {data['name']}!", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == '📋 أزاري')
def list_btns(message):
    uid = message.from_user.id
    c.execute('SELECT name FROM buttons WHERE user_id=?', (uid,))
    btns = c.fetchall()
    if not btns:
        return bot.send_message(uid, "❌ لا توجد أزرار!")
    markup = types.InlineKeyboardMarkup()
    for b in btns:
        markup.add(types.InlineKeyboardButton(b[0], callback_data=f"show_{b[0]}"))
    bot.send_message(uid, "📋 أزرارك:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('show_'))
def show_btn(call):
    name = call.data.replace('show_', '')
    c.execute('SELECT content FROM buttons WHERE user_id=? AND name=?', (call.from_user.id, name))
    res = c.fetchone()
    if res:
        bot.send_message(call.message.chat.id, f"📄 **{name}**\n\n{res[0]}", parse_mode='Markdown')
    bot.answer_callback_query(call.id)

print("🤖 البوت يعمل على Railway...")
bot.infinity_polling()
