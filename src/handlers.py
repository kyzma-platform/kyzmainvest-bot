from database import MongoDB
from bot_commands import bot_commands

from dotenv import load_dotenv
from os import getenv
import telebot
from telebot import types, custom_filters
import time
import random

class Handlers:
    """ Class for handling bot commands"""
    def __init__(self):
        load_dotenv()
        self.database = MongoDB()
        self.bot = telebot.TeleBot(getenv("BOT_TOKEN"))
        self.bot_token = getenv("BOT_TOKEN")
        self.admin_id = getenv("ADMIN_ID")
        self.bot_commands = bot_commands
        self.pashalko = "Взаиморозщеты🦗"
        self.set_commands()
        
    def log(self, message, user_id):
        """ Log messages to the admin in bot chat """
        user_access_level = self.database.get_access_level(user_id)
        if user_access_level == "admin":
            self.bot.send_message(self.admin_id, message)
        
    def set_commands(self):
        """ Set bot commands"""
        self.bot.delete_my_commands()
        commands = [telebot.types.BotCommand(command, description) for command, description in self.bot_commands.items()]
        self.bot.set_my_commands(commands)

    def create_keyboard(self):
        """ Create custom keyboard for the bot """
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton(self.pashalko))
        return markup
        
    def start(self, message):
        """ Start the bot"""
        username = message.from_user.username
        user_id = message.from_user.id
        self.database.add_user(username, user_id)        
        self.bot.reply_to(message, "Поздравляем! Вы подписались на KyZma InVest.", reply_markup=self.create_keyboard())
        self.log(f"User @{username} started the bot", user_id)
        
    def send_help(self, message):
        """ Send available commands to the user """
        help_text = "Доступные команды: \n"
        for key in self.bot_commands:
            help_text += "/" + key + ": "
            help_text += self.bot_commands[key] + "\n"
        self.bot.reply_to(message, help_text)
        self.log(f"User @{message.from_user.username} used /help", message.from_user.id)
        
    def farm_coin(self, message):
        """ Farm coins for the user"""
        user_id = message.from_user.id
        print(user_id)
        current_time = time.time()
        user = self.database.find_user(user_id)
        
        if user is None:
            self.bot.reply_to(message, "Вас нет в базе данных. Напишите /start")
        else:
            if current_time - user['last_farm_time'] < 3600:
                remaining_time = 3600 - (current_time - user['last_farm_time'])
                remaining_minutes = remaining_time // 60
                remaining_seconds = remaining_time % 60
                self.bot.reply_to(message, f"Вы можете фармить снова через {int(remaining_minutes)} минут и {int(remaining_seconds)} секунд.")
                self.log(f"User @{message.from_user.username} farmed too early", user_id)
            else:
                coins = random.randint(1, 30)
                user['coins'] += coins
                user['last_farm_time'] = current_time
                self.database.update_user(user_id, user)
                print(f"User {user['nickname']} farmed {coins} coins. Total: {user['coins']}")
                self.bot.reply_to(message, f"Вы заработали {coins} KyZmaCoin! У вас теперь {user['coins']} KyZmaCoin.")
                self.log(f"User @{message.from_user.username} farmed {coins} coins.\nTotal: {user['coins']} coins.", user_id)
                
    def send_top_users(self, message):
        """ Send top 10 users by coins """
        users = self.database.find_users()
        sorted_users = sorted(users, key=lambda x: x['coins'], reverse=True)
        top_users_message = "Топ-10 пользователей по KyZmaCoin:\n"
        for i, user in enumerate(sorted_users[:10], start=1):
            top_users_message += f"{i}. {user['nickname']} - {user['coins']} KyZmaCoin\n"
        if not sorted_users:
            top_users_message = "Пока нет пользователей."
        self.bot.reply_to(message, top_users_message)
        self.log(f"User @{message.from_user.username} used /top", message.from_user.id)
        
    def vzaimorozchety(self, message):
        """ Взаиморозщеты🦗 """
        self.bot.reply_to(message, "Взаиморозщеты🦗")
        
    def setup_handlers(self):
        """ Setup bot handlers"""
        @self.bot.message_handler(commands=['start'])
        def start(message):
            self.start(message)
            
        @self.bot.message_handler(commands=['help'])
        def help(message):
            self.send_help(message)
        
        @self.bot.message_handler(commands=['farm'])
        def farm(message):
            self.farm_coin(message)
            
        @self.bot.message_handler(commands=['top'])
        def top(message):
            self.send_top_users(message)
            
        @self.bot.message_handler(func=lambda message: message.text == self.pashalko)
        def handle_text(message):
            self.vzaimorozchety(message)