import telebot
from cmd import handle_hrk, handle_plan, handle_info, handle_start, handle_stripe

#Initialize the Telegram bot
bot = telebot.TeleBot("7195510626:AAHdF4spBrcmWPPx9-1gogU1yKM1Rs5qe-s")


# Register command handlers with bot instance explicitly passed
bot.message_handler(func=lambda message: message.text.split()[0].lower().lstrip('/.!') == 'hrk')(lambda message: handle_hrk(message, bot))
bot.message_handler(func=lambda message: message.text.split()[0].lower().lstrip('/.!') == 'st')(lambda message: handle_stripe(message, bot))
bot.message_handler(func=lambda message: message.text.split()[0].lower().lstrip('/.!') == 'plan')(lambda message: handle_plan(message, bot))
bot.message_handler(func=lambda message: message.text.split()[0].lower().lstrip('/.!') == 'info')(lambda message: handle_info(message, bot))
bot.message_handler(func=lambda message: message.text.split()[0].lower().lstrip('/.!') == 'start')(lambda message: handle_start(message, bot))

# Start the bot
if __name__ == "__main__":
    print("Bot is running...")
    bot.polling()
