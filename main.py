import telebot
import requests
import random
import json
import threading
from flask import Flask, request

# Load bot tokens from token.txt
def load_tokens(filename):
    with open(filename, 'r') as file:
        tokens = [line.strip() for line in file]
    return tokens

# Array of emojis
my_emojis = ["👍", "❤", "🔥", "🥰", "👏", "😁", "🤔", "🤯", "😱", "🎉", "🤩", "🙏", "👌", "😍", "❤‍🔥", "🌚", "💯", "🤣", "💔", "😐", "🇮🇳", "😈", "😴", "😭", "🤓", "😇", "🤝", "🤗", "🫡", "🤪", "🗿", "🆒", "💘", "😘", "😎", "🇳🇵"]

# Additional emojis
more_emojis = ["🎈", "🍕", "🌟", "🚀", "🐱", "🌈", "💡", "🍔", "🎶", "📚", "🎨", "⚽", "🍦", "🌻", "🚲", "🏖️", "🎮", "🍩", "🍹", "💻", "🔑", "🎁", "🏆", "📷", "⏰", "💼", "🎳", "🚗", "🎭", "🍓", "🎊", "📝", "💰", "🛫", "🍀", "📱", "🌊"]

# Combine emojis
all_emojis = my_emojis + more_emojis

# Function to send reaction using provided URL
def send_reaction(bot, chat_id, message_id):
    # Select a random emoji
    do_emoji = random.choice(all_emojis)
    
    # Set up the reaction data
    data = {
        'chat_id': chat_id,
        'message_id': message_id,
        'reaction': json.dumps([
            {
                'type': 'emoji',
                'emoji': do_emoji,
                'is_big': True
            }
        ])
    }
    
    # Construct the URL for sending reaction
    url = f'https://api.telegram.org/bot{bot.token}/setMessageReaction'
    
    # Send POST request to the URL
    response = requests.post(url, json=data)
    
    # Print response
    print(response.text)

# Function to handle messages for each bot
def handle_message(bot):
    @bot.message_handler(func=lambda message: True)
    def handle_msg(message):
        send_reaction(bot, message.chat.id, message.message_id)
    
    # Start polling
    bot.polling()

# Flask app initialization
app = Flask(__name__)

# Main route to keep the script alive
@app.route('/')
def index():
    return 'Server is running!'

# Main function
if __name__ == "__main__":
    # Load bot tokens
    tokens = load_tokens("token.txt")
    
    # Create bot instances
    bots = [telebot.TeleBot(token) for token in tokens]
    
    # Start threads for each bot to handle messages
    threads = []
    for bot in bots:
        thread = threading.Thread(target=handle_message, args=(bot,))
        threads.append(thread)
        thread.start()
    
    # Start Flask app
    app.run(host='0.0.0.0', port=8080)
