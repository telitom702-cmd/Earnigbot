import telebot
from telebot import types
import json
import os
import datetime

# ================= CONFIG =================
BOT_TOKEN = 'YOUR_BOT_TOKEN'
ADMIN_ID = 123456789

bot = telebot.TeleBot(BOT_TOKEN)

# ================= FILES =================
USERS_FILE = 'users.json'
TASKS_FILE = 'tasks.json'
SETTINGS_FILE = 'settings.json'

# ================= JSON =================
def load_json(file, default):
    if not os.path.exists(file):
        with open(file, 'w') as f:
            json.dump(default, f)
        return default
    with open(file) as f:
        return json.load(f)

def save_json(file, data):
    with open(file, 'w') as f:
        json.dump(data, f, indent=4)

def get_users(): return load_json(USERS_FILE, {})
def save_users(data): save_json(USERS_FILE, data)

def get_tasks(): return load_json(TASKS_FILE, [])
def save_tasks(data): save_json(TASKS_FILE, data)

# ================= SETTINGS =================
DEFAULT_SETTINGS = {
    "refer_bonus": 5,
    "min_withdraw": 50,
    "daily_bonus": 1,
    "channels": [],
    "currency": "৳",
    "payment_channel": "@yourchannel"
}

def get_settings(): return load_json(SETTINGS_FILE, DEFAULT_SETTINGS)
def save_settings(data): save_json(SETTINGS_FILE, data)

# ================= STATE =================
user_states = {}
temp_data = {}

# ================= MENU =================
def main_menu(uid):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("💰 Balance", "📋 Tasks")
    kb.add("🎁 Daily Bonus", "👫 Refer")
    kb.add("💳 Withdraw", "🏆 Leaderboard")
    if str(uid) == str(ADMIN_ID):
        kb.add("🔐 Admin Panel")
    return kb

# ================= START =================
@bot.message_handler(commands=['start'])
def start(msg):
    uid = str(msg.chat.id)
    users = get_users()

    if uid not in users:
        users[uid] = {
            "name": msg.from_user.first_name,
            "balance": 0,
            "refer": 0,
            "completed": [],
            "last_bonus": None
        }
        save_users(users)

    bot.send_message(uid, "👋 Welcome!", reply_markup=main_menu(uid))

# ================= TASK SHOW =================
@bot.message_handler(func=lambda m: m.text == "📋 Tasks")
def tasks_menu(msg):
    uid = str(msg.chat.id)
    users = get_users()
    tasks = get_tasks()

    done = users[uid].get("completed", [])
    kb = types.InlineKeyboardMarkup()

    for i, t in enumerate(tasks):
        if not t.get("active", True):
            continue
        if i not in done:
            kb.add(types.InlineKeyboardButton(
                f"Task {i+1} (+{t['reward']})",
                callback_data=f"task_{i}"
            ))

    bot.send_message(uid, "📋 Tasks:", reply_markup=kb)

# ================= CALLBACK =================
@bot.callback_query_handler(func=lambda call: True)
def cb(call):
    uid = str(call.message.chat.id)

    # --- VIEW TASK ---
    if call.data.startswith("task_"):
        i = int(call.data.split("_")[1])
        t = get_tasks()[i]

        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("Submit", callback_data=f"submit_{i}"))

        bot.send_message(uid, f"{t['text']}\nReward: {t['reward']}", reply_markup=kb)

    # --- SUBMIT ---
    elif call.data.startswith("submit_"):
        i = call.data.split("_")[1]
        user_states[uid] = f"proof_{i}"
        bot.send_message(uid, "📸 Send screenshot")

    # ================= ADMIN =================

    elif call.data == "admin_manage":
        if uid != str(ADMIN_ID): return
        tasks = get_tasks()

        kb = types.InlineKeyboardMarkup()
        for i, t in enumerate(tasks):
            st = "🟢" if t.get("active", True) else "🔴"
            kb.add(types.InlineKeyboardButton(
                f"{st} Task {i+1}",
                callback_data=f"manage_{i}"
            ))

        bot.send_message(uid, "🛠 Manage:", reply_markup=kb)

    elif call.data.startswith("manage_"):
        i = int(call.data.split("_")[1])
        t = get_tasks()[i]

        kb = types.InlineKeyboardMarkup()
        kb.add(
            types.InlineKeyboardButton("✏️ Text", callback_data=f"editT_{i}"),
            types.InlineKeyboardButton("💰 Reward", callback_data=f"editR_{i}")
        )
        kb.add(
            types.InlineKeyboardButton("🔁 Toggle", callback_data=f"toggle_{i}"),
            types.InlineKeyboardButton("❌ Delete", callback_data=f"del_{i}")
        )

        bot.send_message(uid, f"{t['text']}\n{t['reward']}", reply_markup=kb)

    elif call.data.startswith("toggle_"):
        i = int(call.data.split("_")[1])
        tasks = get_tasks()
        tasks[i]['active'] = not tasks[i].get("active", True)
        save_tasks(tasks)
        bot.answer_callback_query(call.id, "Updated")

    elif call.data.startswith("editT_"):
        i = int(call.data.split("_")[1])
        user_states[uid] = f"editT_{i}"
        bot.send_message(uid, "New text:")

    elif call.data.startswith("editR_"):
        i = int(call.data.split("_")[1])
        user_states[uid] = f"editR_{i}"
        bot.send_message(uid, "New reward:")

    elif call.data.startswith("del_"):
        i = int(call.data.split("_")[1])
        tasks = get_tasks()
        tasks.pop(i)
        save_tasks(tasks)

        users = get_users()
        for u in users:
            new = []
            for t in users[u]['completed']:
                if t == i: continue
                elif t > i: new.append(t-1)
                else: new.append(t)
            users[u]['completed'] = new

        save_users(users)
        bot.answer_callback_query(call.id, "Deleted")

# ================= TEXT =================
@bot.message_handler(func=lambda m: True)
def txt(msg):
    uid = str(msg.chat.id)

    if uid in user_states:
        state = user_states[uid]
        text = msg.text
        tasks = get_tasks()

        if state.startswith("editT_"):
            i = int(state.split("_")[1])
            tasks[i]['text'] = text
            save_tasks(tasks)
            bot.send_message(uid, "Updated")

        elif state.startswith("editR_"):
            i = int(state.split("_")[1])
            try:
                tasks[i]['reward'] = float(text)
                save_tasks(tasks)
                bot.send_message(uid, "Updated")
            except:
                bot.send_message(uid, "Invalid")

        del user_states[uid]

# ================= PHOTO =================
@bot.message_handler(content_types=['photo'])
def photo(msg):
    uid = str(msg.chat.id)

    if uid in user_states and user_states[uid].startswith("proof_"):
        i = int(user_states[uid].split("_")[1])
        t = get_tasks()[i]

        kb = types.InlineKeyboardMarkup()
        kb.add(
            types.InlineKeyboardButton("✅ Approve", callback_data=f"ok_{uid}_{i}"),
            types.InlineKeyboardButton("❌ Reject", callback_data=f"no_{uid}")
        )

        bot.send_photo(ADMIN_ID, msg.photo[-1].file_id,
                       caption=f"User {uid}\nTask {i}",
                       reply_markup=kb)

        bot.send_message(uid, "Sent to admin")
        del user_states[uid]

print("Bot running...")
bot.infinity_polling()
