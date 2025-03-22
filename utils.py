import os
import json
import time
from datetime import datetime, timedelta

# Owner's Telegram ID
OWNER_ID = 6460703454

# File to store user data
USER_DATA_FILE = "user_data.json"

# Plans configuration
PLANS = {
    "1": {"name": "𝗕𝗮𝘀𝗶𝗰 𝗣𝗿𝗲𝗺𝗶𝘂𝗺", "cooldown": 15, "hourly_limit": 50},
    "2": {"name": "𝗠𝗶𝗱-𝗧𝗶𝗲𝗿 𝗣𝗿𝗲𝗺𝗶𝘂𝗺", "cooldown": 13, "hourly_limit": 100},
    "3": {"name": "𝗧𝗼𝗽-𝗧𝗶𝗲𝗿 𝗣𝗿𝗲𝗺𝗶𝘂𝗺", "cooldown": 7, "hourly_limit": 150}
}
FREE_COOLDOWN = 30
FREE_HOURLY_LIMIT = 10

if not os.path.exists(USER_DATA_FILE):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump({"premium_users": {}, "free_users": {}}, f)

def load_user_data():
    try:
        with open(USER_DATA_FILE, 'r') as f:
            content = f.read().strip()
            return json.loads(content) if content else {"premium_users": {}, "free_users": {}}
    except (json.JSONDecodeError, FileNotFoundError):
        return {"premium_users": {}, "free_users": {}}

def save_user_data(data):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(data, f)

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
            return False, f"𝗣𝗹𝗲𝗮𝘀𝗲 𝘄𝗮𝗶𝘁 {FREE_COOLDOWN - int(now.timestamp() - last_check)} 𝘀𝗲𝗰𝗼𝗻�_d𝘀."
        if len(checks) >= FREE_HOURLY_LIMIT:
            return False, "𝗛𝗼𝘂𝗿𝗹𝘆 𝗹𝗶𝗺𝗶𝘁 𝗼𝗳 𝟭𝟬 𝗰𝗵𝗲𝗰𝗸𝘀 𝗿𝗲𝗮𝗰𝗵𝗲𝗱. 𝗕𝗲𝗰𝗼𝗺𝗲 𝗽𝗿𝗲𝗺𝗶𝘂𝗺 𝗳𝗼𝗿 𝗺𝗼𝗿𝗲."
        
        free_users[str(user_id)]["last_check"] = now.timestamp()
        free_users[str(user_id)]["checks"].append(now.isoformat())
        save_user_data(user_data)
        return True, None

def update_loading_bar(chat_id, message_id, start_time, done_event, bot):
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