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
        if user_access_level == "user":
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
        # coins
        common_coins = random.randint(5, 30)
        rare_coins = 50
        coins = 0
        
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
                if random.random() < 0.1:
                    coins = rare_coins
                else:
                    coins = common_coins
                user['coins'] += coins
                user['last_farm_time'] = current_time
                self.database.update_user(user_id, user)
                print(f"User {user['nickname']} farmed {coins} coins. Total: {user['coins']}")
                self.bot.reply_to(message, f"Вы заработали {coins} KyZmaCoin! У вас теперь {user['coins']} KyZmaCoin.")
                self.log(f"User @{message.from_user.username} farmed {coins} coins.\nTotal: {user['coins']} coins.", user_id)
                
    def send_top_users(self, message):
        """ Send top 10 users by coins, excluding the admin """
        users = self.database.find_users()
        
        users = [user for user in users if user['user_id'] != int(self.admin_id)]
        
        sorted_users = sorted(users, key=lambda x: x['coins'], reverse=True)
        
        top_users_message = "Топ-10 пользователей по KyZmaCoin:\n"
        
        for i, user in enumerate(sorted_users[:10], start=1):
            top_users_message += f"{i}. {user['nickname']} - {user['coins']} KyZmaCoin\n"
        
        if not sorted_users:
            top_users_message = "Пока нет пользователей."
        
        # Send the message
        self.bot.reply_to(message, top_users_message)
        self.log(f"User @{message.from_user.username} used /top", message.from_user.id)

        
    def give_all_users_1000_coins(self, message):
        """ Give 1000 coins to all users """
        if message.from_user.id != int(self.admin_id):
            self.bot.reply_to(message, "Иди нахуй ты не админ.")
        # Retrieve all users from the database
        users = self.database.find_users()
        chat_id = message.chat.id

        # Iterate through all users and add 1000 coins
        for user in users:
        # Check if the user is not the admin (just in case you want to exclude admin from getting coins)
            if user['user_id'] == int(self.admin_id):
                updated_user = {
                    "coins": user["coins"] + 1000  # Update only the 'coins' field
                }

            # Update the user's coins using their user_id (no modification to _id)
            self.database.update_user(user['user_id'], updated_user)
        
        # Notify the admin that the operation has been completed
        self.bot.send_message(chat_id, f"<b>Увага! Роздача ПОТУЖНОЇ ТИСЯЧІ для гемблінгу!</b>", parse_mode="HTML")
        self.log(f"Admin @{message.from_user.username} gave 1000 coins to all users", message.from_user.id)
   

    def slot_machine(self, message):
        """ Simple Slot Machine Game with fruits as the results"""
        user_id = message.from_user.id
        user = self.database.find_user(user_id)

        if user is None:
            self.bot.reply_to(message, "Вас нет в базе данных. Напишите /start")
            return

        # Check if the user's balance is less than or equal to 0
        if user['coins'] <= 0:
            self.bot.reply_to(message, "У вас недостаточно KyZmaCoin для игры. Пожалуйста, заработайте монеты.")
            return

        # Send a dice roll animation to simulate the slot machine spinning
        self.bot.send_dice(message.chat.id, emoji="🎰")
        time.sleep(1)

        fruits = ["🍒", "🍋", "🍊", "🍉", "🍇", "🍓", "🍍", "🍑"]

        # Generate 3 random fruits for the slot machine result
        results = [random.choice(fruits) for _ in range(3)]

        # 20% chance of all three fruits being the same
        if random.random() < 0.2:
            selected_fruit = random.choice(fruits)
            results = [selected_fruit] * 3

        # Build the result message
        message_result = f"Вы прокрутили слоты и получили: {results[0]} - {results[1]} - {results[2]}\n"

        # Check if the user wins
        if results[0] == results[1] == results[2]:
            win_amount = 0
            # 5% chance of winning a large amount
            if random.random() < 0.05:
                win_amount = 250
            else:
                # Normal win range between 15 and 40
                win_amount = random.randint(15, 40)
            user['coins'] += win_amount
            message_result += f"Поздравляем! Вы выиграли {win_amount} KyZmaCoin! У вас теперь {user['coins']} KyZmaCoin."
        else:
            lose_amount = random.randint(10, 25)
            user['coins'] -= lose_amount
            message_result += f"Увы, вы проиграли {lose_amount} KyZmaCoin. У вас теперь {user['coins']} KyZmaCoin."

        # Update the user's balance in the database
        self.database.update_user(user_id, user)

        # Send the result to the user
        self.bot.reply_to(message, message_result)
        self.log(f"User @{message.from_user.username} played the slot machine", user_id)


        
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
            
        @self.bot.message_handler(commands=['slot'])
        def slot(message):
            self.slot_machine(message)
            
        @self.bot.message_handler(commands=['give'])
        def give(message):
            self.give_coins(message)
            
        @self.bot.message_handler(commands=['rozdacha_tyshchi'])
        def rozdacha(message):
            self.give_all_users_1000_coins(message)
            
        @self.bot.message_handler(func=lambda message: message.text == self.pashalko)
        def handle_text(message):
            self.vzaimorozchety(message)