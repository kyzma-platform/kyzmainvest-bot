from database import MongoDB
from bot.bot_commands import user_bot_commands, admin_bot_commands
from bot.bot_replies import bot_replies
from games.roulette import Roulette
from games.slots import Slots
from games.farm import Farm

from dotenv import load_dotenv
from os import getenv
import telebot
from telebot import types
import time

class Handlers:
    """ Class for handling bot commands"""
    def __init__(self):
        load_dotenv()
        self.database = MongoDB()
        self.roulette = Roulette()
        self.slots = Slots()
        self.farm = Farm()
        self.bot = telebot.TeleBot(getenv("BOT_TOKEN"))
        self.bot_token = getenv("BOT_TOKEN")
        self.admin_id = getenv("ADMIN_ID")
        
        self.user_bot_commands = user_bot_commands
        self.admin_bot_commands = admin_bot_commands
        self.bot_replies = bot_replies
        self.set_commands()
        
    def log(self, message, user_id):
        """ Log messages to the admin in bot chat 

            log(message, user_id)
        """
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
        markup.add(types.KeyboardButton(self.bot_replies['pashalko']))
        return markup
        
    def start(self, message):
        """ Start the bot"""
        username = message.from_user.username
        user_id = message.from_user.id
        self.database.add_user(username, user_id)
            
        self.bot.reply_to(message, self.bot_replies['welcome'], reply_markup=self.create_keyboard())
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
                
    def send_top_users(self, message):
        """ Send top 10 users by coins, excluding the admin """
        users = self.database.find_users()
        
        users = [user for user in users if user['user_id'] != int(self.admin_id)]
        
        sorted_users = sorted(users, key=lambda x: x['coins'], reverse=True)
        
        top_users_message = "Топ слоняр в KyZma InVest:\n"
        
        for i, user in enumerate(sorted_users[:10], start=1):
            top_users_message += f"{i}. {user['nickname']} - {user['coins']} KyZmaCoin\n"
        
        if not sorted_users:
            top_users_message = self.bot_replies['error_no_users']
        
        self.bot.reply_to(message, top_users_message)
        self.log(f"User @{message.from_user.username} used /top", message.from_user.id)
        
    # def send_bottom_users(self, message):
    #     """ Send users with negative balance """
    #     users = self.database.find_users()

    #     users = [user for user in users if user['user_id'] != int(self.admin_id)]
        
    #     negative_balance_users = [user for user in users if user['coins'] < 0]
        
    #     sorted_users = sorted(negative_balance_users, key=lambda x: x['coins'])

    #     if not sorted_users:
    #         self.bot.reply_to(message, self.bot_replies['error_no_users'])
    #         return

    #     bottom_users_message = "Топ гоев в KyZma InVest:\n"

    #     for i, user in enumerate(sorted_users[:10], start=1):
    #         bottom_users_message += f"{i}. {user['nickname']} - {user['coins']} KyZmaCoin\n"

    #     self.bot.reply_to(message, bottom_users_message)
    #     self.log(f"User @{message.from_user.username} used /goys", message.from_user.id)
        
    def send_debtors(self, message):
        """ Send a list of users with debt in descending order """
        users = self.database.find_users()
        
        # Filter users with debt > 0 and exclude the admin
        debtors = [user for user in users if user['debt'] > 0 and user['user_id'] != int(self.admin_id)]
        
        # Sort debtors by debt in descending order
        sorted_debtors = sorted(debtors, key=lambda x: x['debt'], reverse=True)
        
        debtors_message = "Список должников в KyZma InVest:\n"
        
        for i, debtor in enumerate(sorted_debtors, start=1):
            debtors_message += f"{i}. {debtor['nickname']} - {debtor['debt']} KyZmaCoin\n"
        
        if not sorted_debtors:
            debtors_message = "Никто не имеет задолженностей."
        
        self.bot.reply_to(message, debtors_message)
        self.log(f"User @{message.from_user.username} used /goys", message.from_user.id)


    def give_all_users_1000_coins(self, message):
        """ Give 1000 coins to all users """
        if message.from_user.id != int(self.admin_id):
            self.bot.reply_to(message, self.bot_replies['not_admin'])
        else:
            users = self.database.find_users()
            chat_id = message.chat.id

            for user in users:
                updated_user = {
                    "coins": user["coins"] + 1000 
                }

                self.database.update_user(user['user_id'], updated_user)
            
            self.bot.send_message(chat_id, self.bot_replies['rozdacha'], parse_mode="HTML")
      
    def check_balance(self, message, user_id):
        """ Check the user's balance """
        user = self.database.find_user_id(user_id)
        self.bot.reply_to(message, f"У вас {user['coins']} KyZmaCoin.")
        self.log(f"User @{message.from_user.username} checked their balance", user_id)

    def vzaimorozchety(self, message):
        """ Взаиморозщеты🦗 """
        self.bot.reply_to(message, "Взаиморозщеты🦗")
        
    # * Debt System *
    def borrow_money(self, message):
        user_id = message.from_user.id
        user = self.database.find_user_id(user_id)
        
        if user['debt_limit_reached']:
            self.bot.reply_to(message, "Вы исчерпали лимит долга в 1.000.000 KyZmaCoin. Пожалуйста, погасите долг, чтобы взять ещё.")
            return

        parts = message.text.split()
        if len(parts) != 2 or not parts[1].isdigit():
            self.bot.reply_to(message, "Неверный формат. Используйте: /borrow <amount>")
            return

        amount = int(parts[1])

        if amount <= 0 or amount > 1_000_000 - user['debt']:
            self.bot.reply_to(message, "Вы не можете взять такую сумму. Лимит долга: 1.000.000 KyZmaCoin.")
            return

        user['coins'] += amount
        user['debt'] += amount

        if user['debt'] >= 1_000_000:
            user['debt_limit_reached'] = True

        self.database.update_user(user_id, user)
        self.bot.reply_to(message, f"Вы взяли {amount} KyZmaCoin в долг. Ваш текущий долг: {user['debt']} KyZmaCoin.")
        self.log(f"User @{message.from_user.username} took a dept {user['debt']} coins")
        
    def repay_debt(self, message):
        user_id = message.from_user.id
        user = self.database.find_user_id(user_id)

        if user['debt'] == 0:
            self.bot.reply_to(message, "У вас нет долгов.")
            return

        parts = message.text.split()
        if len(parts) != 2 or not parts[1].isdigit():
            self.bot.reply_to(message, "Неверный формат. Используйте: /repay <amount>")
            return

        amount = int(parts[1])

        if amount <= 0:
            self.bot.reply_to(message, "Сумма должна быть больше нуля.")
            return

        if amount > user['coins']:
            self.bot.reply_to(message, "У вас недостаточно средств для погашения этой суммы.")
            return

        if amount > user['debt']:
            amount = user['debt']

        user['coins'] -= amount
        user['debt'] -= amount

        if user['debt'] < 1_000_000:
            user['debt_limit_reached'] = False

        self.database.update_user(user_id, user)
        self.bot.reply_to(message, f"Вы погасили {amount} KyZmaCoin. Ваш текущий долг: {user['debt']} KyZmaCoin.")
        self.log(f"User @{message.from_user.username} repayed debt {amount} coins.")
        
    def check_debt(self, message):
        user_id = message.from_user.id
        user = self.database.find_user_id(user_id)
        self.bot.reply_to(message, f"Ваш текущий долг: {user['debt']} KyZmaCoin.")
        self.log(f"User @{message.from_user.username} checked their debt")

    # ^ Admin commands ^
        
    def all_users(self, message):
        """ Get all users"""
        if message.from_user.id != int(self.admin_id):
            self.bot.reply_to(message, self.bot_replies['not_admin'])
            return
        else:
            users = self.database.find_users()
            message = ""
            for index, user in enumerate(users, start=1):
                message += f"{index}. @{user['nickname']} - {user['coins']} coins\n"
            self.bot.send_message(self.admin_id, message)
            
    def get_user(self, message, nickname):
        """ Get user by nickname"""
        if message.from_user.id != int(self.admin_id):
            self.bot.reply_to(message, self.bot_replies['not_admin'])
            return
        else:
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
        if message.from_user.id != int(self.admin_id):
            self.bot.reply_to(message, self.bot_replies['not_admin'])
            return
        else:
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
        
    def remove_coins(self, message):
        """ Remove coins from the user"""
        if message.from_user.id != int(self.admin_id):
            self.bot.reply_to(message, self.bot_replies['not_admin'])
            return
        else:
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
            user_id = message.from_user.id
            user = self.database.find_user_id(user_id)
            current_time = time.time()
            print(current_time)
            
            game_result = self.farm.farm_coin(message, user, current_time)
            if game_result is not None:
                self.database.update_user(user_id, game_result)
                self.log(f"User @{message.from_user.username} farmed {game_result} coins.")
            else:
                print("Game result is None, skipping database update.")
            
        @self.bot.message_handler(commands=['slonyari'])
        def top(message):
            self.send_top_users(message)
            
        @self.bot.message_handler(commands=['slot'])
        def slot(message):
            # self.slot_machine(message)
            user_id = message.from_user.id
            user = self.database.find_user_id(user_id)
            game_result = self.slots.slot_machine(message, user)
            if game_result is not None:
                self.database.update_user(user_id, game_result)
            else:
                print("Game result is None, skipping database update.")
            
        @self.bot.message_handler(commands=['roulette'])
        def roulette(message):
            user_id = message.from_user.id
            user = self.database.find_user_id(user_id)
            game_result = self.roulette.roulette_game(message, user)
            if game_result is not None:
                self.database.update_user(user_id, game_result)
            else:
                print("Game result is None, skipping database update.")
            
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
            self.send_debtors(message)
            
        @self.bot.message_handler(func=lambda message: message.text == self.bot_replies['pashalko'])
        def handle_text(message):
            self.vzaimorozchety(message)
            
        # ^ Admin commands ^
        
        @self.bot.message_handler(commands=['all_users'])
        def get_all_users(message):
            self.all_users(message)
            
        @self.bot.message_handler(commands=['find'])
        def get_user_handler(message):
            parts = message.text.split()

            if len(parts) != 2:
                self.bot.reply_to(message, "Неверный формат. Используйте: /find <nickname>")
                return

            nickname = parts[1]
            self.get_user(message, nickname)
                
        @self.bot.message_handler(commands=['give'])
        def give_coins_handler(message):
            self.give_coins(message)
                
        @self.bot.message_handler(commands=['remove'])
        def remove_coins_handler(message):
            self.remove_coins(message)
            
        @self.bot.message_handler(commands=['borrow'])
        def borrow_handler(message):
            self.borrow_money(message)

        @self.bot.message_handler(commands=['repay'])
        def repay_handler(message):
            self.repay_debt(message)

        @self.bot.message_handler(commands=['debt'])
        def debt_handler(message):
            self.check_debt(message)

