import telebot
from telebot import types
import json
import os
import datetime

# ================= CONFIGURATION =================
BOT_TOKEN = 'PUT_YOUR_NEW_TOKEN_HERE'
ADMIN_ID = 5828992083

bot = telebot.TeleBot(BOT_TOKEN)

# ================= DATABASE FILES =================
USERS_FILE = 'users.json'
TASKS_FILE = 'tasks.json'
SETTINGS_FILE = 'settings.json'

# --- Data Management Functions ---
def load_json(filename, default_data):
    if not os.path.exists(filename):
        with open(filename, 'w') as f:
            json.dump(default_data, f, indent=4)
        return default_data
    with open(filename, 'r') as f:
        return json.load(f)

def save_json(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

# FIXED (no recursion bug)
def get_users(): return load_json(USERS_FILE, {})

def save_users_real(data):
    save_json(USERS_FILE, data)

def get_tasks(): return load_json(TASKS_FILE, [])
def save_tasks(data): save_json(TASKS_FILE, data)

# --- SETTINGS ---
DEFAULT_SETTINGS = {
    "refer_bonus": 5.0,
    "min_withdraw": 50,
    "daily_bonus": 1.0,
    "payment_channel": "@starbotbd56",
    "channels": ["@shiyam7449266", "@starbotbd56", "@shiyam744"],
    "currency": "৳"
}

def get_settings(): return load_json(SETTINGS_FILE, DEFAULT_SETTINGS)
def save_settings(data): save_json(SETTINGS_FILE, data)

# ================= STATES =================
user_states = {}
temp_data = {}

# ================= CHECK JOIN (FIXED) =================
def check_join(user_id):
    settings = get_settings()
    not_joined = []
    try:
        for channel in settings['channels']:
            try:
                stat = bot.get_chat_member(channel, user_id).status
                if stat not in ['creator', 'administrator', 'member']:
                    not_joined.append(channel)
            except Exception:
                pass
        return len(not_joined) == 0
    except Exception:
        return False

# ================= KEYBOARD =================
def main_menu_keyboard(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    markup.add(
        types.KeyboardButton('💰 Balance'),
        types.KeyboardButton('🎁 Daily Bonus'),
        types.KeyboardButton('📋 Tasks'),
        types.KeyboardButton('👫 Refer'),
        types.KeyboardButton('💳 Withdraw'),
        types.KeyboardButton('🏆 Leaderboard')
    )

    if str(user_id) == str(ADMIN_ID):
        markup.add(types.KeyboardButton('🔐 Admin Panel'))

    return markup

# ================= START =================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = str(message.chat.id)
    users = get_users()
    settings = get_settings()
    name = message.from_user.first_name

    if user_id not in users:
        users[user_id] = {
            'name': name,
            'balance': 0,
            'refer': 0,
            'completed': [],
            'last_bonus': None
        }
        save_users_real(users)

    if check_join(user_id):
        bot.send_message(user_id, f"👋 Welcome {name}",
                         reply_markup=main_menu_keyboard(user_id))
    else:
        bot.send_message(user_id, "⚠️ Please join channels first!")

# ================= BALANCE =================
@bot.message_handler(func=lambda m: m.text == '💰 Balance')
def balance_menu(message):
    users = get_users()
    settings = get_settings()
    u = users.get(str(message.chat.id), {})
    bot.send_message(message.chat.id,
                     f"💰 Balance: {u.get('balance',0)} {settings['currency']}")

# ================= DAILY BONUS =================
@bot.message_handler(func=lambda m: m.text == '🎁 Daily Bonus')
def daily_bonus(message):
    users = get_users()
    settings = get_settings()
    uid = str(message.chat.id)

    today = str(datetime.date.today())

    if users[uid].get('last_bonus') == today:
        bot.send_message(uid, "❌ Already claimed today")
        return

    users[uid]['balance'] += settings['daily_bonus']
    users[uid]['last_bonus'] = today
    save_users_real(users)

    bot.send_message(uid, "🎁 Bonus received!")

# ================= REFER =================
@bot.message_handler(func=lambda m: m.text == '👫 Refer')
def refer_menu(message):
    link = f"https://t.me/{bot.get_me().username}?start={message.chat.id}"
    bot.send_message(message.chat.id, f"🔗 Your link:\n{link}")

# ================= LEADERBOARD (FIXED) =================
@bot.message_handler(func=lambda m: m.text == '🏆 Leaderboard')
def leaderboard(message):
    users = get_users()
    settings = get_settings()

    sorted_users = sorted(users.items(),
                          key=lambda x: x[1].get('balance', 0),
                          reverse=True)[:10]

    msg = "🏆 Top Users:\n\n"
    for idx, (uid, data) in enumerate(sorted_users):
        msg += f"{idx+1}. {data.get('name','User')} - {data.get('balance',0)} {settings['currency']}\n"

    bot.send_message(message.chat.id, msg)

# ================= ADMIN =================
@bot.message_handler(func=lambda m: m.text == '🔐 Admin Panel')
def admin_panel(message):
    if str(message.chat.id) != str(ADMIN_ID):
        return

    bot.send_message(message.chat.id, "👮 Admin Panel Active")

# ================= BOT START =================
print("Bot running...")
bot.infinity_polling()
