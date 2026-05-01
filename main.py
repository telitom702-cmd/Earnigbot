import telebot
from telebot import types
import json
import os
import datetime

# ================= CONFIGURATION =================
BOT_TOKEN = '8534427928:AAEeOKXj4L8bpkvw2FiOcwuQiPdwR5c9aOg'  # আপনার টোকেন
ADMIN_ID = 5828992083              # আপনার টেলিগ্রাম ID (Integer হিসেবে)

bot = telebot.TeleBot(BOT_TOKEN)

# ================= DATABASE FILES =================
USERS_FILE = 'users.json'
TASKS_FILE = 'tasks.json'
SETTINGS_FILE = 'settings.json'

# --- Data Management Functions ---
def load_json(filename, default_data):
    if not os.path.exists(filename):
        with open(filename, 'w') as f: json.dump(default_data, f, indent=4)
        return default_data
    with open(filename, 'r') as f: return json.load(f)

def save_json(filename, data):
    with open(filename, 'w') as f: json.dump(data, f, indent=4)

# Load Data Helpers
def get_users(): return load_json(USERS_FILE, {})
def save_users(data): save_users(USERS_FILE, data) # Note: Fixed logic in wrapper below
def save_users_real(data): save_json(USERS_FILE, data) # Renamed for clarity

def get_tasks(): return load_json(TASKS_FILE, [])
def save_tasks(data): save_json(TASKS_FILE, data)

# --- SETTINGS MANAGEMENT (The "Box" for Editing) ---
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

# Global Variables for States
user_states = {} 
temp_data = {}   

# ================= HELPER FUNCTIONS =================

def check_join(user_id):
    settings = get_settings()
    not_joined = []
    try:
        for channel in settings['channels']:
            try:
                stat = bot.get_chat_member(channel, user_id).status
                if stat not in ['creator', 'administrator', 'member']:
                    not_joined.append(channel)
            except:
                pass
        return len(not_joined) == 0
    except:
        return False

# --- UPDATED KEYBOARD FUNCTION (লজিক পরিবর্তন করা হয়েছে) ---
def main_menu_keyboard(user_id):
    # row_width=2 মানে প্রতি লাইনে ২টা করে বাটন থাকবে, এতে বাটন ছোট এবং সুন্দর দেখাবে
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    # বাটনগুলো সুন্দরভাবে সাজানো
    btn_bal = types.KeyboardButton('💰 Balance')
    btn_bonus = types.KeyboardButton('🎁 Daily Bonus')
    btn_task = types.KeyboardButton('📋 Tasks')
    btn_refer = types.KeyboardButton('👫 Refer')
    btn_withdraw = types.KeyboardButton('💳 Withdraw')
    btn_top = types.KeyboardButton('🏆 Leaderboard')
    
    markup.add(btn_bal, btn_bonus, btn_task, btn_refer, btn_withdraw, btn_top)
    
    # শুধুমাত্র এডমিন হলে এই বাটনটি যোগ হবে
    if str(user_id) == str(ADMIN_ID):
        markup.add(types.KeyboardButton('🔐 Admin Panel')) # স্পেশাল এডমিন বাটন
        
    return markup

# ================= HANDLERS START =================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = str(message.chat.id)
    users = get_users()
    settings = get_settings()
    name = message.from_user.first_name

    # Registration
    if user_id not in users:
        referrer = message.text.split()[1] if len(message.text.split()) > 1 else None
        users[user_id] = {
            'name': name, 
            'balance': 0, 
            'refer': 0, 
            'completed': [],
            'last_bonus': None
        }
        
        # Refer Logic
        if referrer and referrer in users and referrer != user_id:
            bonus = settings['refer_bonus']
            users[referrer]['balance'] += bonus
            users[referrer]['refer'] += 1
            try:
                bot.send_message(referrer, f"🎉 **New Referral!**\nYou earned {bonus}{settings['currency']}!", parse_mode='Markdown')
            except: pass
        save_users_real(users)
    
    # Check Join
    if check_join(user_id):
        # এখানে user_id পাস করা হলো যাতে বাটন ফিল্টার করা যায়
        bot.send_message(user_id, f"👋 Welcome **{name}**!\n\n✨ Earn Money by completing simple tasks!", reply_markup=main_menu_keyboard(user_id), parse_mode='Markdown')
    else:
        send_join_message(user_id)

def send_join_message(user_id):
    settings = get_settings()
    markup = types.InlineKeyboardMarkup()
    for i, ch in enumerate(settings['channels']):
        markup.add(types.InlineKeyboardButton(f"👉 Join Channel {i+1}", url=f"https://t.me/{ch.replace('@','')}"))
    
    markup.add(types.InlineKeyboardButton("✅ Checked Joined", callback_data="check_join_stat"))
    bot.send_message(user_id, "⚠️ **Must Join All Channels to Start!**", reply_markup=markup, parse_mode='Markdown')

# --- User Menu Handlers ---

@bot.message_handler(func=lambda m: m.text == '💰 Balance')
def balance_menu(message):
    user_id = str(message.chat.id)
    users = get_users()
    settings = get_settings()
    bal = users[user_id]['balance']
    ref = users[user_id]['refer']
    text = f"👤 **My Wallet**\n\n🆔 ID: `{user_id}`\n💰 Balance: **{bal} {settings['currency']}**\n👥 Referrals: **{ref}**"
    bot.send_message(user_id, text, parse_mode='Markdown')

@bot.message_handler(func=lambda m: m.text == '👫 Refer')
def refer_menu(message):
    user_id = str(message.chat.id)
    settings = get_settings()
    link = f"https://t.me/{bot.get_me().username}?start={user_id}"
    bot.send_message(user_id, f"🚀 **Invite & Earn!**\n\nPer Refer: **{settings['refer_bonus']} {settings['currency']}**\n\nYour Link:\n`{link}`", parse_mode='Markdown')

@bot.message_handler(func=lambda m: m.text == '🎁 Daily Bonus')
def daily_bonus(message):
    user_id = str(message.chat.id)
    users = get_users()
    settings = get_settings()
    
    today = str(datetime.date.today())
    last_bonus = users[user_id].get('last_bonus')
    
    if last_bonus == today:
        bot.send_message(user_id, "❌ **Already Claimed Today!**\nCome back tomorrow.")
    else:
        bonus = settings['daily_bonus']
        users[user_id]['balance'] += bonus
        users[user_id]['last_bonus'] = today
        save_users_real(users)
        bot.send_message(user_id, f"🎁 **Daily Bonus Claimed!**\nYou received {bonus} {settings['currency']}.")

@bot.message_handler(func=lambda m: m.text == '🏆 Leaderboard')
def leaderboard(message):
    users = get_users()
    settings = get_settings()
    sorted_users = sorted(users.items(), key=lambda x: x[1]['balance'], reverse=True)[:10]
    
    msg = "🏆 **TOP 10 USERS** 🏆\n\n"
    for idx, (uid, data) in enumerate(sorted_users):
        msg += f"{idx+1}. {data['name']} - {data['balance']} {settings['currency']}\n"
    
    bot.send_message(message.chat.id, msg)

@bot.message_handler(func=lambda m: m.text == '💳 Withdraw')
def withdraw_req(message):
    user_id = str(message.chat.id)
    users = get_users()
    settings = get_settings()
    
    bal = users[user_id]['balance']
    min_wd = settings['min_withdraw']
    
    if bal < min_wd:
        bot.send_message(user_id, f"❌ Minimum Withdraw: **{min_wd} {settings['currency']}**\nYour Balance: {bal} {settings['currency']}")
        return

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(" বিকাশ (Bkash)", callback_data="wd_bkash"))
    markup.add(types.InlineKeyboardButton(" নগদ (Nagad)", callback_data="wd_nagad"))
    markup.add(types.InlineKeyboardButton(" রিচার্জ (Recharge)", callback_data="wd_recharge"))
    
    bot.send_message(user_id, "💸 Select Payment Method:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == '📋 Tasks')
def show_tasks_menu(message):
    user_id = str(message.chat.id)
    users = get_users()
    tasks = get_tasks()
    settings = get_settings()
    
    completed_list = users[user_id].get('completed', [])
    markup = types.InlineKeyboardMarkup()
    
    count = 0
    for idx, task in enumerate(tasks):
        if idx not in completed_list:
            markup.add(types.InlineKeyboardButton(f"Task {idx+1} (+{task['reward']}{settings['currency']})", callback_data=f"view_task_{idx}"))
            count += 1
            
    if count == 0:
        bot.send_message(message.chat.id, "🎉 All tasks completed!")
    else:
        bot.send_message(message.chat.id, "📋 **Click to Complete:**", reply_markup=markup)

# --- Admin Panel Handler ---
# এখানে আমরা নাম পরিবর্তন করেছি বাটনের সাথে মিল রাখার জন্য '🔐 Admin Panel'
@bot.message_handler(func=lambda m: m.text == '🔐 Admin Panel')
def admin_panel(message):
    if str(message.chat.id) != str(ADMIN_ID):
        return # এডমিন না হলে কিছুই করবে না
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("⚙️ Settings Box", callback_data="admin_settings"),
        types.InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"),
        types.InlineKeyboardButton("➕ Add Task", callback_data="admin_add_task"),
        types.InlineKeyboardButton("🗑 Reset Tasks", callback_data="admin_del_tasks")
    )
    
    users = get_users()
    bot.send_message(message.chat.id, f"👮‍♂️ **Admin Dashboard**\nTotal Users: {len(users)}", reply_markup=markup)

# ================= CALLBACK HANDLERS =================

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = str(call.message.chat.id)
    users = get_users()
    settings = get_settings()

    # --- Join Check ---
    if call.data == "check_join_stat":
        if check_join(user_id):
            bot.delete_message(user_id, call.message.message_id)
            # এখানেও user_id পাস করা হলো
            bot.send_message(user_id, "✅ Success! Menu unlocked.", reply_markup=main_menu_keyboard(user_id))
        else:
            bot.answer_callback_query(call.id, "❌ Join all channels first!", show_alert=True)

    # --- Withdraw System ---
    elif call.data.startswith("wd_"):
        method = call.data.split("_")[1]
        user_states[user_id] = "waiting_wd_number"
        temp_data[user_id] = {"method": method}
        bot.send_message(user_id, f"🔢 Enter your **{method}** Number:")

    # --- Task System ---
    elif call.data.startswith("view_task_"):
        idx = int(call.data.split("_")[2])
        tasks = get_tasks()
        task = tasks[idx]
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Submit Proof", callback_data=f"submit_task_{idx}"))
        bot.send_message(user_id, f"📝 **Task:**\n{task['text']}\n\nReward: {task['reward']} {settings['currency']}", reply_markup=markup)

    elif call.data.startswith("submit_task_"):
        idx = int(call.data.split("_")[2])
        user_states[user_id] = f"waiting_proof_{idx}"
        bot.send_message(user_id, "📸 Send screenshot now.")

    # --- Admin Approval ---
    elif call.data.startswith("approve_"):
        _, uid, amount, tidx = call.data.split("_")
        amount = float(amount)
        tidx = int(tidx)
        
        u_data = get_users()
        if uid in u_data:
            u_data[uid]['balance'] += amount
            if 'completed' not in u_data[uid]: u_data[uid]['completed'] = []
            u_data[uid]['completed'].append(tidx)
            save_users_real(u_data)
            
            bot.edit_message_caption(chat_id=ADMIN_ID, message_id=call.message.message_id, caption=f"{call.message.caption}\n✅ **PAID**")
            bot.send_message(uid, f"✅ Task Approved! You got {amount} {settings['currency']}")
            
    elif call.data.startswith("reject_"):
        uid = call.data.split("_")[1]
        bot.edit_message_caption(chat_id=ADMIN_ID, message_id=call.message.message_id, caption=f"{call.message.caption}\n❌ **REJECTED**")
        bot.send_message(uid, "❌ Task Rejected.")

    # --- ADMIN SETTINGS BOX ---
    elif call.data == "admin_settings":
        if str(user_id) != str(ADMIN_ID): return
        
        s = get_settings()
        msg = (f"⚙️ **SETTINGS BOX**\n\n"
               f"1️⃣ Refer Bonus: {s['refer_bonus']}\n"
               f"2️⃣ Min Withdraw: {s['min_withdraw']}\n"
               f"3️⃣ Daily Bonus: {s['daily_bonus']}\n"
               f"4️⃣ Payment Channel: {s['payment_channel']}\n"
               f"5️⃣ Channels: {len(s['channels'])} Active")
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("✏️ Set Refer Bonus", callback_data="set_refer"))
        markup.add(types.InlineKeyboardButton("✏️ Set Min Withdraw", callback_data="set_min_wd"))
        markup.add(types.InlineKeyboardButton("✏️ Set Daily Bonus", callback_data="set_daily"))
        markup.add(types.InlineKeyboardButton("➕ Add Channel", callback_data="add_channel"))
        markup.add(types.InlineKeyboardButton("➖ Remove Channel", callback_data="rem_channel"))
        markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="admin_back"))
        
        bot.edit_message_text(msg, chat_id=user_id, message_id=call.message.message_id, reply_markup=markup, parse_mode='Markdown')

    elif call.data in ["set_refer", "set_min_wd", "set_daily", "add_channel", "rem_channel"]:
        user_states[user_id] = call.data
        prompts = {
            "set_refer": "Enter new Refer Bonus amount:",
            "set_min_wd": "Enter new Minimum Withdraw amount:",
            "set_daily": "Enter new Daily Bonus amount:",
            "add_channel": "Enter channel username (e.g. @mychannel):",
            "rem_channel": "Enter channel username to remove:"
        }
        bot.send_message(user_id, prompts[call.data])

    elif call.data == "admin_back":
         bot.delete_message(user_id, call.message.message_id)
         # Re-trigger admin panel logic manually since we don't have message object easily, 
         # but simpler to just send new menu or edit text. Here sending new menu:
         markup = types.InlineKeyboardMarkup(row_width=2)
         markup.add(
            types.InlineKeyboardButton("⚙️ Settings Box", callback_data="admin_settings"),
            types.InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"),
            types.InlineKeyboardButton("➕ Add Task", callback_data="admin_add_task"),
            types.InlineKeyboardButton("🗑 Reset Tasks", callback_data="admin_del_tasks")
         )
         bot.send_message(user_id, "👮‍♂️ **Admin Dashboard**", reply_markup=markup)
         
    elif call.data == "admin_broadcast":
        user_states[user_id] = "waiting_broadcast"
        bot.send_message(user_id, "📢 Enter message to broadcast:")

    elif call.data == "admin_add_task":
        user_states[user_id] = "waiting_task_text"
        bot.send_message(user_id, "➕ Enter Task Description:")
        
    elif call.data == "admin_del_tasks":
        save_tasks([])
        bot.answer_callback_query(call.id, "Tasks reset!", show_alert=True)

# ================= INPUT HANDLERS =================

@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_id = str(message.chat.id)
    text = message.text
    
    # --- ADMIN ACTIONS ---
    if str(user_id) == str(ADMIN_ID) and user_id in user_states:
        state = user_states[user_id]
        settings = get_settings()
        
        if state == "set_refer":
            settings['refer_bonus'] = float(text)
            save_settings(settings)
            bot.send_message(user_id, "✅ Refer Bonus Updated!")
            
        elif state == "set_min_wd":
            settings['min_withdraw'] = float(text)
            save_settings(settings)
            bot.send_message(user_id, "✅ Min Withdraw Updated!")
            
        elif state == "set_daily":
            settings['daily_bonus'] = float(text)
            save_settings(settings)
            bot.send_message(user_id, "✅ Daily Bonus Updated!")
            
        elif state == "add_channel":
            if text.startswith("@"):
                settings['channels'].append(text)
                save_settings(settings)
                bot.send_message(user_id, "✅ Channel Added!")
            else:
                bot.send_message(user_id, "❌ Must start with @")
                
        elif state == "rem_channel":
            if text in settings['channels']:
                settings['channels'].remove(text)
                save_settings(settings)
                bot.send_message(user_id, "✅ Channel Removed!")
            else:
                bot.send_message(user_id, "❌ Channel not found!")

        elif state == "waiting_broadcast":
            users = get_users()
            count = 0
            for uid in users:
                try:
                    bot.send_message(uid, f"📢 **NOTICE**\n\n{text}", parse_mode='Markdown')
                    count += 1
                except: pass
            bot.send_message(user_id, f"Sent to {count} users.")
            
        elif state == "waiting_task_text":
            temp_data['new_task_text'] = text
            user_states[user_id] = "waiting_task_reward"
            bot.send_message(user_id, "💰 Enter Reward Amount:")
            return # Keep state
            
        elif state == "waiting_task_reward":
            tasks = get_tasks()
            try:
                tasks.append({"text": temp_data['new_task_text'], "reward": float(text)})
                save_tasks(tasks)
                bot.send_message(user_id, "✅ Task Added!")
            except:
                bot.send_message(user_id, "❌ Invalid amount.")
            
        del user_states[user_id]
        return

    # --- USER ACTIONS ---
    if user_id in user_states:
        state = user_states[user_id]
        
        if state == "waiting_wd_number":
            users = get_users()
            settings = get_settings()
            info = temp_data[user_id]
            amount = users[user_id]['balance']
            
            # Deduct Balance
            users[user_id]['balance'] = 0
            save_users_real(users)
            
            # Notify Admin Channel
            msg = (f"🔔 **Withdraw Request**\n"
                   f"👤 User: {users[user_id]['name']} (`{user_id}`)\n"
                   f"💰 Amount: {amount} {settings['currency']}\n"
                   f"🏦 Method: {info['method']}\n"
                   f"📱 Number: `{text}`")
            
            bot.send_message(settings['payment_channel'], msg, parse_mode='Markdown')
            bot.send_message(user_id, "✅ Request Submitted! Please wait for payment.")
            del user_states[user_id]

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = str(message.chat.id)
    if user_id in user_states and user_states[user_id].startswith("waiting_proof_"):
        idx = int(user_states[user_id].split("_")[2])
        tasks = get_tasks()
        settings = get_settings()
        
        caption = (f"📸 **Proof Submitted**\n"
                   f"👤 User: {message.from_user.first_name} (`{user_id}`)\n"
                   f"💰 Claim: {tasks[idx]['reward']} {settings['currency']}")
        
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}_{tasks[idx]['reward']}_{idx}"),
            types.InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}")
        )
        
        bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=caption, reply_markup=markup, parse_mode='Markdown')
        bot.send_message(user_id, "✅ Proof sent to admin!")
        del user_states[user_id]

print("🤖 Super Bot Started...")
bot.infinity_polling()
