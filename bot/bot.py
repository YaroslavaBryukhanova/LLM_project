from telebot import TeleBot
from bot.authentication import Authentication
from bot.pdf_handler import PDFHandler
from bot.choose_handler import ChooseHandler
from utilis.config import TELEGRAM_TOKEN
from .database import cursor, conn
from .globals import authenticated_users

# Initialize the Telegram bot
bot = TeleBot(TELEGRAM_TOKEN)

# Initialize the cache and active files
# authenticated_users = {}
# cache = {}
# active_files = {}

authentication = Authentication(bot)
pdf_handler = PDFHandler(bot)
choose_handler = ChooseHandler(bot)

# Start the bot
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Welcome! I'm a chatbot that can help you to recap lectures material. You can upload a PDF file and ask questions about it. Moreover, by default you already have a huge PDF file containing info about Introduction to AI course. You may try this bot by interacting with this document! Let's get started!")
    bot.send_message(chat_id, "Are you a new user? Reply 'yes' to register or 'no' to log in.")


# Remind option
@bot.message_handler(commands=['remind'])
def remind(message):
    chat_id = message.chat.id
    #get the user username from the database
    cursor.execute("SELECT username, password FROM users WHERE chat_id = ?", (chat_id,))
    username, password = cursor.fetchone()
    bot.send_message(chat_id, f"Your current username - {username}, and password - {password}.")
    bot.send_message(chat_id, "Please log in with your username and password by typing /start and selecting 'no' to log in.")


# Choose option 
@bot.message_handler(commands=['choose'])
def choose(message):
    choose_handler.handle_choose_command(message)
# Handle file selection
@bot.message_handler(func=lambda message: message.chat.id in authenticated_users and "file_options" in authenticated_users[message.chat.id])
def handle_file_selection(message):
    choose_handler.handle_file_selection(message)


# Handle registration
@bot.message_handler(func=lambda message: message.chat.id in authenticated_users and not authenticated_users[message.chat.id]["authenticated"] and authenticated_users[message.chat.id]["registration"])
def handle_registration(message):  
    authentication.handle_registration(message)
# Handle login
@bot.message_handler(func=lambda message: message.chat.id in authenticated_users and not authenticated_users[message.chat.id]["authenticated"] and not authenticated_users[message.chat.id]["registration"])
def handle_login(message):
    authentication.handle_login(message)
# Handle initial response during registration or login
@bot.message_handler(func=lambda message: message.chat.id not in authenticated_users)
def handle_initial_response(message):
    authentication.handle_initial_response(message)


# Handle PDF upload
@bot.message_handler(content_types=['document'])
def handle_pdf_upload(message):
    pdf_handler.handle_pdf_upload(message)
# Handle question answering
@bot.message_handler(func=lambda message: authenticated_users.get(message.chat.id, {}).get("authenticated"))
def handle_question(message):
    pdf_handler.handle_question(message)
