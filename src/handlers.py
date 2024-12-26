from database import MongoDB
from bot_commands import user_bot_commands, admin_bot_commands

from dotenv import load_dotenv
from os import getenv
import telebot
from telebot import types
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
        self.user_bot_commands = user_bot_commands
        self.admin_bot_commands = admin_bot_commands
        self.pashalko = "Взаиморозщеты🦗"
        self.set_commands()
        
        # farm and slot settigs
        self.farm_rare_coins = 50
        self.farm_rare_chance = 0.1
        self.slot_jackpot_chance = 0.05
        self.slot_win_chance = 0.2
        
    def log(self, message, user_id):
        """ Log messages to the admin in bot chat """
        user_access_level = self.database.get_access_level(user_id)
        if user_access_level == "user":
            self.bot.send_message(self.admin_id, message)
        
    def set_commands(self):
        """ Set bot commands"""
        self.bot.delete_my_commands()
        commands = [telebot.types.BotCommand(command, description) for command, description in self.user_bot_commands.items()]
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
        if message.from_user.id == int(self.admin_id):
            for key in self.admin_bot_commands:
                help_text += "/" + key + ": "
                help_text += self.admin_bot_commands[key] + "\n"
        else:
            for key in self.user_bot_commands:
                help_text += "/" + key + ": "
                help_text += self.user_bot_commands[key] + "\n"
        self.bot.reply_to(message, help_text)
        self.log(f"User @{message.from_user.username} used /help", message.from_user.id)
        
    def farm_coin(self, message):
        """ Farm coins for the user"""
        # coins

        coins = 0
        
        user_id = message.from_user.id
        print(user_id)
        current_time = time.time()
        user = self.database.find_user_id(user_id)
        
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
                if random.random() < self.farm_rare_chance:
                    coins = self.farm_rare_coins
                else:
                    coins = random.randint(5, 30)
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
        
        top_users_message = "Топ слоняр в KyZma InVest:\n"
        
        for i, user in enumerate(sorted_users[:10], start=1):
            top_users_message += f"{i}. {user['nickname']} - {user['coins']} KyZmaCoin\n"
        
        if not sorted_users:
            top_users_message = "Пока нет пользователей."
        
        # Send the message
        self.bot.reply_to(message, top_users_message)
        self.log(f"User @{message.from_user.username} used /top", message.from_user.id)
        
    def send_bottom_users(self, message):
        """ Send users with negative balance, excluding the admin """
        users = self.database.find_users()

        # Exclude the admin user
        users = [user for user in users if user['user_id'] != int(self.admin_id)]
        
        # Filter for users with a negative balance
        negative_balance_users = [user for user in users if user['coins'] < 0]
        
        # Sort users by their negative balance in ascending order (most negative first)
        sorted_users = sorted(negative_balance_users, key=lambda x: x['coins'])

        if not sorted_users:
            self.bot.reply_to(message, "Нет пользователей с отрицательным балансом.")
            return

        # Prepare the message with the users with negative balance
        bottom_users_message = "Топ гоев в KyZma InVest:\n"

        for i, user in enumerate(sorted_users[:10], start=1):
            bottom_users_message += f"{i}. {user['nickname']} - {user['coins']} KyZmaCoin\n"

        # Send the message to the user
        self.bot.reply_to(message, bottom_users_message)
        self.log(f"User @{message.from_user.username} used /goys", message.from_user.id)


        
    def give_all_users_1000_coins(self, message):
        """ Give 1000 coins to all users """
        if message.from_user.id != int(self.admin_id):
            self.bot.reply_to(message, "Иди нахуй ты не админ.")
        else:
            # Retrieve all users from the database
            users = self.database.find_users()
            chat_id = message.chat.id

            # Iterate through all users and add 1000 coins
            for user in users:
            # Check if the user is not the admin (just in case you want to exclude admin from getting coins)
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
        user = self.database.find_user_id(user_id)

        if user is None:
            self.bot.reply_to(message, "Вас нет в базе данных. Напишите /start")
            return

        if user['coins'] <= 0:
            self.bot.reply_to(message, "У вас недостаточно KyZmaCoin для игры. Пожалуйста, заработайте монеты.")
            return

        self.bot.send_dice(message.chat.id, emoji="🎰")
        time.sleep(1)

        fruits = ["🍒", "🍋", "🍊", "🍉", "🍇", "🍓", "🍍", "🍑"]

        results = [random.choice(fruits) for _ in range(3)]

        if random.random() < self.slot_win_chance:
            selected_fruit = random.choice(fruits)
            results = [selected_fruit] * 3

        message_result = f"Вы прокрутили слоты и получили: {results[0]} - {results[1]} - {results[2]}\n"

        if results[0] == results[1] == results[2]:
            win_amount = 0
            if random.random() < self.slot_jackpot_chance:
                win_amount = 250
            else:
                win_amount = random.randint(15, 40)
            user['coins'] += win_amount
            message_result += f"Поздравляем! Вы выиграли {win_amount} KyZmaCoin! У вас теперь {user['coins']} KyZmaCoin."
        else:
            lose_amount = random.randint(10, 25)
            user['coins'] -= lose_amount
            message_result += f"Увы, вы проиграли {lose_amount} KyZmaCoin. У вас теперь {user['coins']} KyZmaCoin."

        self.database.update_user(user_id, user)

        self.bot.reply_to(message, message_result)
        self.log(f"User @{message.from_user.username} played the slot machine", user_id)
      
    def check_balance(self, message, user_id):
        """ Check the user's balance """
        user = self.database.find_user_id(user_id)
        self.bot.reply_to(message, f"У вас {user['coins']} KyZmaCoin.")
        self.log(f"User @{message.from_user.username} checked their balance", user_id)

    def vzaimorozchety(self, message):
        """ Взаиморозщеты🦗 """
        self.bot.reply_to(message, "Взаиморозщеты🦗")
        
    # ^ Admin commands ^
        
    def change_chances(self, message):
        """ Command for the admin to change farm and slot chances """
        if message.from_user.id != int(self.admin_id):
            self.bot.reply_to(message, "Только админ может изменить шансы.")
            return
        else:
            self.bot.reply_to(message, "Стандарные шансы:\nself.farm_rare_chance = 0.1\nself.slot_jackpot_chance = 0.05\nself.slot_win_chance = 0.2")
            parts = message.text.split()
            
            if len(parts) != 4:
                self.bot.reply_to(message, "Неверный формат. Используйте: /change_chances <farm_rare_chance> <slot_win_chance> <slot_jackpot_chance>")
                return
            try:
                new_farm_rare_chance = float(parts[1])
                new_slot_win_chance = float(parts[2])
                new_slot_jackpot_chance = float(parts[3])

                if not (0 <= new_farm_rare_chance <= 1) or not (0 <= new_slot_win_chance <= 1) or not (0 <= new_slot_jackpot_chance <= 1):
                    self.bot.reply_to(message, "Шансы должны быть числами от 0 до 1.")
                    return

                self.farm_rare_chance = new_farm_rare_chance
                self.slot_win_chance = new_slot_win_chance
                self.slot_jackpot_chance = new_slot_jackpot_chance

                self.bot.reply_to(message, f"Шансы успешно изменены:\n"
                                        f"Фарм редкой монеты: {new_farm_rare_chance * 100}%\n"
                                        f"Шанс на выигрыш в слоте: {new_slot_win_chance * 100}%\n"
                                        f"Шанс на джекпот в слоте: {new_slot_jackpot_chance * 100}%")
                self.log(f"Admin @{message.from_user.username} changed the farm and slot chances.", message.from_user.id)
        
            except ValueError:
                self.bot.reply_to(message, "Пожалуйста, введите правильные числовые значения для шансов.")
                
    def all_users(self):
        """ Get all users"""
        users = self.database.find_users()
        message = ""
        for index, user in enumerate(users, start=1):
            message += f"{index}. @{user['nickname']} - {user['coins']} coins\n"
        self.bot.send_message(self.admin_id, message)
        
    def get_user(self, message, nickname):
        """ Get user by nickname"""
        user = self.database.find_user_nickname(nickname)
        parts = message.text.split()
        if len(parts) != 2:
            self.bot.reply_to(message, "Неверный формат. Используйте: /find <nickname>")
            return None
        if user is None:
            self.bot.reply_to(message, "Пользователь не найден.")
            return None
        else:
            message = f"Nickname: @{user['nickname']}\nID: {user["user_id"]}\nCoins: {user['coins']}\nLast farm time: {user['last_farm_time']}\nAccess level: {user['access_level']}"
            self.bot.send_message(self.admin_id, message)
            
    def give_coins(self, message):
        """ Give coins to the user"""
        parts = message.text.split()
        if len(parts) != 3:
            self.bot.reply_to(message, "Неверный формат. Используйте: /give <nickname> <amount>")
            return
        nickname = parts[1]
        amount = int(parts[2])
        user = self.database.find_user_nickname(nickname)
        if user is None:
            self.bot.reply_to(message, "Пользователь не найден.")
            return
        user['coins'] += amount
        self.database.update_user(user['user_id'], user)
        self.bot.reply_to(message, f"Вы успешно дали {amount} KyZmaCoin пользователю @{nickname}.")
        self.log(f"Admin @{message.from_user.username} gave {amount} coins to @{nickname}", message.from_user.id)
        
    def remove_coins(self, message):
        """ Remove coins from the user"""
        parts = message.text.split()
        if len(parts) != 3:
            self.bot.reply_to(message, "Неверный формат. Используйте: /remove <nickname> <amount>")
            return
        nickname = parts[1]
        amount = int(parts[2])
        user = self.database.find_user_nickname(nickname)
        if user is None:
            self.bot.reply_to(message, "Пользователь не найден.")
            return
        user['coins'] -= amount
        self.database.update_user(user['user_id'], user)
        self.bot.reply_to(message, f"Вы успешно забрали {amount} KyZmaCoin у пользователя @{nickname}.")
        self.log(f"Admin @{message.from_user.username} removed {amount} coins from @{nickname}", message.from_user.id)
        
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
            
        @self.bot.message_handler(commands=['balance'])
        def balance(message):
            self.check_balance(message, message.from_user.id)
            
        @self.bot.message_handler(commands=['goys'])
        def send_goys(message):
            self.send_bottom_users(message)
            
        @self.bot.message_handler(func=lambda message: message.text == self.pashalko)
        def handle_text(message):
            self.vzaimorozchety(message)
            
        # ^ Admin commands ^
            
        @self.bot.message_handler(commands=['change_chances'])
        def change_chances_handler(message):
            if message.from_user.id != int(self.admin_id):
                self.bot.reply_to(message, "Только админ может изменить шансы.")
            else:
                self.change_chances(message)
            
        @self.bot.message_handler(commands=['all_users'])
        def get_all_users(message):
            if message.from_user.id != int(self.admin_id):
                self.bot.reply_to(message, "Только админ может получить список всех пользователей.")
            else:
                self.all_users()
            
        @self.bot.message_handler(commands=['find'])
        def get_user_handler(message):
            if message.from_user.id != int(self.admin_id):
                self.bot.reply_to(message, "Только админ может получить информацию о пользователе.")
            else:
                parts = message.text.split()

                if len(parts) != 2:
                    self.bot.reply_to(message, "Неверный формат. Используйте: /find <nickname>")
                    return

                nickname = parts[1]
                self.get_user(message, nickname)
                
        @self.bot.message_handler(commands=['give'])
        def give_coins_handler(message):
            if message.from_user.id != int(self.admin_id):
                self.bot.reply_to(message, "Только админ может дать монеты.")
            else:
                self.give_coins(message)
                
        @self.bot.message_handler(commands=['remove'])
        def remove_coins_handler(message):
            if message.from_user.id != int(self.admin_id):
                self.bot.reply_to(message, "Только админ может забрать монеты.")
            else:
                self.remove_coins(message)
