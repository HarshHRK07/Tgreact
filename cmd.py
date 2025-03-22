from telebot import TeleBot
import time
import threading
from datetime import datetime, timedelta
from payrix import process_payment, get_bin_info
from stripe import process_stripe_payment
from cardhandler import parse_cc_input
from utils import can_user_check, load_user_data, save_user_data, update_loading_bar, OWNER_ID, PLANS, FREE_COOLDOWN, FREE_HOURLY_LIMIT

def handle_hrk(message, bot: TeleBot):
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
        bot.reply_to(message, "𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗳𝗼𝗿𝗺𝗮𝘁. 𝗨𝘀𝗲: /𝗵𝗿𝗸 𝗰𝗮𝗿𝗱|𝗠𝗠|𝗬𝗬[𝗬𝗬]|𝗖𝗩𝗩 𝗼𝗿 /𝗵𝗿𝗸 𝗰𝗮𝗿𝗱/𝗠𝗠/𝗬𝗬/𝗖𝗩𝗩\n"
                     "𝗘𝘅𝗮𝗺𝗽𝗹𝗲𝘀: 1234123412341234|12|24|123 or 1234/1234/1234/1234/12/24/123")
        return
    
    done_event = threading.Event()
    try:
        cc_input = message.text.split(" ", 1)[1]
        cc_data = parse_cc_input(cc_input)
        
        if not cc_data:
            bot.reply_to(message, "𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗖𝗖 𝗳𝗼𝗿𝗺𝗮𝘁. 𝗨𝘀𝗲: /𝗵𝗿𝗸 𝗰𝗮𝗿𝗱|𝗠𝗠|𝗬𝗬[𝗬𝗬]|𝗖𝗩𝗩 𝗼𝗿 /𝗵𝗿𝗸 𝗰𝗮𝗿𝗱/𝗠𝗠/𝗬𝗬/𝗖𝗩𝗩\n"
                        "𝗦𝘂𝗽𝗽𝗼𝗿𝘁𝗲𝗱: 1234-1234-1234-1234|12|24|123 or 1234123412341234/12/24/123 or 349807466349303|03/27|968")
            return
            
        card_number, exp_month, exp_year, cvv = cc_data
        loading_message = bot.reply_to(message, "𝗣𝗿𝗼𝗰𝗲𝘀𝘀𝗶𝗻𝗴 𝗽𝗮𝘆𝗺𝗲𝗻𝘁...\n[░░░░░░░░░░░░░░░░░░░░] 𝟬%\n𝗘𝗹𝗮𝗽𝘀𝗲𝗱: 𝟬.𝟬𝘀")
        
        loading_thread = threading.Thread(
            target=update_loading_bar,
            args=(message.chat.id, loading_message.message_id, start_time, done_event, bot)
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
                f"𝗚𝗮𝘁𝗲𝘄𝗮𝘆 ⇾ 𝗔𝗨𝗧𝗛\n"
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
                f"𝗚𝗮𝘁𝗲𝘄𝗮𝘆 ⇾ 𝗔𝗨𝗧𝗛\n"
                f"𝗥𝗲𝘀𝗽𝗼𝗻𝘀𝗲 ⇾ {response_msg}\n\n"
                f"𝗕𝗜𝗡 𝗜𝗻𝗳𝗼: {bin_info['brand']} - {bin_info['type']} - {bin_info['sub_type']}\n"
                f"𝗕𝗮𝗻𝗸: {bin_info['bank']}\n"
                f"𝗖𝗼𝘂𝗻𝘁𝗿𝘆: {bin_info['country']}\n\n"
                f"𝗧𝗼𝗼𝗸 {time_taken}"
            )
        
        bot.edit_message_text(chat_id=message.chat.id, message_id=loading_message.message_id, text=response)
    
    except Exception as e:
        done_event.set()
        bot.reply_to(message, "𝗔𝗻 𝗲𝗿𝗿𝗼𝗿 𝗼𝗰𝗰𝘂𝗿𝗿𝗲𝗱. 𝗣𝗹𝗲𝗮𝘀𝗲 𝘁𝗿𝘆 𝗮𝗴𝗮𝗶𝗻.")
        print(f"Error processing command from user {user_id}: {str(e)}")

def handle_stripe(message, bot: TeleBot):
    start_time = time.time()
    user_id = message.from_user.id
    cmd = message.text.split()[0].lstrip('/.!').lower()
    if cmd != "st":
        return
    
    can_check, error_msg = can_user_check(user_id)
    if not can_check:
        bot.reply_to(message, error_msg)
        return
    
    if len(message.text.split(" ", 1)) < 2:
        bot.reply_to(message, "𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗳𝗼𝗿𝗺𝗮𝘁. 𝗨𝘀𝗲: /𝘀𝘁 𝗰𝗮𝗿𝗱|𝗠𝗠|𝗬𝗬[𝗬𝗬]|𝗖𝗩𝗩 𝗼𝗿 /𝘀𝘁 𝗰𝗮𝗿𝗱/𝗠𝗠/𝗬𝗬/𝗖𝗩𝗩\n"
                     "𝗘𝘅𝗮𝗺𝗽𝗹𝗲𝘀: 1234123412341234|12|24|123 or 1234/1234/1234/1234/12/24/123")
        return
    
    done_event = threading.Event()
    try:
        cc_input = message.text.split(" ", 1)[1]
        cc_data = parse_cc_input(cc_input)
        
        if not cc_data:
            bot.reply_to(message, "𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗖𝗖 𝗳𝗼𝗿𝗺𝗮𝘁. �_U𝘀𝗲: /𝘀𝘁 𝗰𝗮𝗿𝗱|𝗠𝗠|𝗬𝗬[𝗬𝗬]|𝗖𝗩𝗩 𝗼𝗿 /𝘀𝘁 𝗰𝗮𝗿𝗱/𝗠𝗠/𝗬𝗬/𝗖𝗩𝗩\n"
                        "𝗦𝘂𝗽𝗽𝗼𝗿𝘁𝗲𝗱: 1234-1234-1234-1234|12|24|123 or 1234123412341234/12/24/123 or 349807466349303|03/27|968")
            return
            
        card_number, exp_month, exp_year, cvv = cc_data
        loading_message = bot.reply_to(message, "𝗣𝗿𝗼𝗰𝗲𝘀𝘀𝗶𝗻𝗴 𝗽𝗮𝘆𝗺𝗲𝗻𝘁...\n[░░░░░░░░░░░░░░░░░░░░] 𝟬%\n𝗘𝗹𝗮𝗽𝘀𝗲𝗱: 𝟬.𝟬𝘀")
        
        loading_thread = threading.Thread(
            target=update_loading_bar,
            args=(message.chat.id, loading_message.message_id, start_time, done_event, bot)
        )
        loading_thread.start()
        
        response_msg = process_stripe_payment(card_number, exp_month, exp_year, cvv)
        bin_info = get_bin_info(card_number)  # From payrix.py
        time_taken = f"{time.time() - start_time:.2f} 𝘀𝗲𝗰𝗼𝗻𝗱𝘀"
        done_event.set()
        
        if response_msg == "𝗖𝗵𝗮𝗿𝗴𝗲𝗱 $𝟭 ✅":
            response = (
                f"𝗔𝗽𝗽𝗿𝗼𝘃𝗲𝗱 ✅\n\n"
                f"𝗖𝗖 ⇾ {card_number}|{exp_month}|{exp_year}|{cvv}\n"
                f"𝗚𝗮𝘁𝗲𝘄𝗮𝘆 ⇾𝐒𝐭𝐫𝐢𝐩𝐞 𝐂𝐡𝐚𝐫𝐠𝐞 $𝟭\n"
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
                f"𝗚𝗮𝘁𝗲𝘄𝗮𝘆 ⇾ 𝐒𝐭𝐫𝐢𝐩𝐞 𝐂𝐡𝐚𝐫𝐠𝐞 $𝟭\n"
                f"𝗥𝗲𝘀𝗽𝗼𝗻𝘀𝗲 ⇾ {response_msg}\n\n"
                f"𝗕𝗜𝗡 𝗜𝗻𝗳𝗼: {bin_info['brand']} - {bin_info['type']} - {bin_info['sub_type']}\n"
                f"𝗕𝗮𝗻𝗸: {bin_info['bank']}\n"
                f"𝗖𝗼𝘂𝗻𝘁𝗿𝘆: {bin_info['country']}\n\n"
                f"𝗧𝗼𝗼𝗸 {time_taken}"
            )
        
        bot.edit_message_text(chat_id=message.chat.id, message_id=loading_message.message_id, text=response)
    
    except Exception as e:
        done_event.set()
        bot.reply_to(message, "𝗔𝗻 𝗲𝗿𝗿𝗼𝗿 𝗼𝗰𝗰𝘂𝗿𝗿𝗲𝗱. 𝗣𝗹𝗲𝗮𝘀𝗲 𝘁𝗿𝘆 𝗮𝗴𝗮𝗶𝗻.")
        print(f"Error processing Stripe command from user {user_id}: {str(e)}")

def handle_plan(message, bot: TeleBot):
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

def handle_info(message, bot: TeleBot):
    user_id = str(message.from_user.id)
    user_data = load_user_data()
    now = datetime.now()

    if int(user_id) == OWNER_ID:
        response = (
    f"👤 User Info: {user_id}\n"
    f"📛 Plan: Owner (Unlimited Access 🚀)\n"
    f"⏳ Cooldown: None\n"
    f"🚀 Hourly Limit: Infinite\n"
    f"✅ Remaining Checks: Unlimited\n"
    f"🔄 Limit Resets In: Not Applicable"
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
    f"👤 User Info: {user_id}\n"
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
            time_until_reset = "𝗥𝗲𝘀𝗲𝘁𝘀 𝗼𝗻 𝗻𝗲𝘅𝘁 �_r𝗲𝗾𝘂𝗲𝘀𝘁"

        response = (
    f"👤 User Info: {user_id}\n"
    f"📛 Plan: Free User\n"
    f"⏳ Cooldown: {FREE_COOLDOWN} seconds\n"
    f"🚀 Hourly Limit: {FREE_HOURLY_LIMIT}\n"
    f"✅ Remaining Checks: {remaining_checks}\n"
    f"🔄 Limit Resets In: {time_until_reset}"
)
    
    bot.reply_to(message, response)

def handle_start(message, bot: TeleBot):
    user_id = message.from_user.id
    response = (
    f"👋 Welcome to HRK's Bot, {message.from_user.first_name}!\n\n"
    f"⚡ Commands:\n"
    f"📌 /hrk card|MM|YY|CVV - Check card (Auth)\n"
    f"📌 /st card|MM|YY|CVV - Check card (Stripe Charge $1)\n\n"
    f"🔹 Examples:\n"
    f"   - 1234-1234-1234-1234|12|24|123\n"
    f"   - 1234/1234/1234/1234/12/24/123\n"
    f"   - 349807466349303|03/27|968\n"
    f"   - 1234123412341234|12|2024|123\n\n"
    f"📌 /info - Plan info\n\n"
    f"🚀 Premium Plans:\n"
    f"🔹 Basic: 15s cooldown, 50/hr\n"
    f"🔹 Mid-Tier: 13s cooldown, 100/hr\n"
    f"🔹 Top-Tier: 7s cooldown, 150/hr\n"
    f"🔄 Free: 30s cooldown, 10/hr"
)
    
    bot.reply_to(message, response)
