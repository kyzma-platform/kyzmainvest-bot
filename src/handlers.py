from database import MongoDB
from bot.bot_commands import user_bot_commands, admin_bot_commands
from bot.bot_replies import bot_replies
from games.roulette import Roulette
from games.slots import Slots
from games.farm import Farm
from bank import Bank
# from admin_handler import AdminHandler

from dotenv import load_dotenv
from os import getenv
import telebot
from telebot import types
import time
import schedule
import threading

class Handlers:
    """ Class for handling bot commands"""
    def __init__(self):
        self.bot = telebot.TeleBot(getenv("BOT_TOKEN"))
        load_dotenv()
        self.database = MongoDB()
        self.roulette = Roulette()
        self.slots = Slots()
        self.farm = Farm()
        self.bank = Bank()
        # self.admin_handler = AdminHandler()
        self.admin_id = getenv("ADMIN_ID")
        self.amnesty_requests = {}
                
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
        self.database.add_user(username, user_id, name=None)
            
        self.bot.reply_to(message, self.bot_replies['welcome'], reply_markup=self.create_keyboard())
        self.log(f"User {username} started the bot", user_id)
        
        
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
        self.log(f"User {message.from_user.username} used /help", message.from_user.id)
                
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
        self.log(f"User {message.from_user.username} used /top", message.from_user.id)
        
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
        self.log(f"User {message.from_user.username} used /goys", message.from_user.id)\
    
    def setup_schedules(self):
        """ Setup the daily reminder to send debt reminders """
        schedule.every().day.at("22:00").do(self.bank.remind_debtors)
        schedule.every(1).hour.do(self.bank.apply_interest_to_all_users)

    def vzaimorozchety(self, message):
        """ Взаиморозщеты🦗 """
        self.bot.reply_to(message, "Взаиморозщеты🦗")
            

    def request_amnesty(self, message):
        """ Start the amnesty request process """
        user_id = message.from_user.id
        if user_id in self.amnesty_requests:
            self.bot.reply_to(message, "Вы уже отправили запрос на амнистию.")
            return
        
        self.bot.reply_to(message, "Что касается вашей амнистии? Опишите, пожалуйста, ситуацию.")
        self.amnesty_requests[user_id] = {'step': 1}

    def collect_amnesty_reason(self, message):
        """ Collect the reason for amnesty """
        user_id = message.from_user.id
        reason = message.text
        if user_id not in self.amnesty_requests or self.amnesty_requests[user_id]['step'] != 1:
            return
        
        # Store the reason and ask for the message
        self.amnesty_requests[user_id]['reason'] = reason
        self.bot.reply_to(message, "Теперь напишите сообщение для администратора, которое вы хотите отправить.")
        self.amnesty_requests[user_id]['step'] = 2

    def collect_amnesty_message(self, message):
        """ Collect the message for amnesty """
        user_id = message.from_user.id
        amnesty_data = self.amnesty_requests.get(user_id)
        
        if not amnesty_data or amnesty_data['step'] != 2:
            return
        
        # Store the message
        amnesty_message = message.text
        amnesty_data['message'] = amnesty_message
        
        # Send the amnesty request to the admin
        self.bot.send_message(self.admin_id, f"Запрос на амнистию от {message.from_user.username}:\n\n"
                                             f"Причина: {amnesty_data['reason']}\n"
                                             f"Сообщение: {amnesty_data['message']}")
        
        # Inform the user and reset the process
        self.bot.reply_to(message, "Ваш запрос на амнистию отправлен админу. Ожидайте ответа.")
        self.amnesty_requests.pop(user_id)

    def setup_handlers(self):
        """ Setup bot handlers"""
        @self.bot.message_handler(commands=['start'])
        def start(message):
            self.start(message)
            self.database.add_new_field()
            
        @self.bot.message_handler(commands=['help'])
        def help(message):
            self.send_help(message)
        
        @self.bot.message_handler(commands=['farm'])
        def farm(message):
            user_id = message.from_user.id
            user = self.database.find_user_id(user_id)
            current_time = time.time()
            
            game_result = self.farm.farm_coin(message, user, current_time)
            if game_result is not None:
                self.database.update_user(user_id, game_result)
                self.log(f"User {message.from_user.username} farmed {game_result} coins.\n\nTotal: {user['coins']}", user_id)
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
                self.log(f"User {message.from_user.username} played slots.", user_id)
            else:
                print("Game result is None, skipping database update.")
            
        @self.bot.message_handler(commands=['roulette'])
        def roulette(message):
            user_id = message.from_user.id
            user = self.database.find_user_id(user_id)
            game_result = self.roulette.roulette_game(message, user)
            if game_result is not None:
                self.database.update_user(user_id, game_result)
                self.log(f"User {message.from_user.username} played roulette.", user_id)
            else:
                print("Game result is None, skipping database update.")
            
        @self.bot.message_handler(commands=['balance'])
        def balance(message):
            self.bank.check_balance(message, message.from_user.id)
            
        @self.bot.message_handler(commands=['goys'])
        def send_goys(message):
            self.send_debtors(message)
            
        @self.bot.message_handler(func=lambda message: message.text == self.bot_replies['pashalko'])
        def handle_text(message):
            self.vzaimorozchety(message)
                        
        @self.bot.message_handler(commands=['borrow'])
        def borrow_handler(message):
            self.bank.borrow_money(message)

        @self.bot.message_handler(commands=['repay'])
        def repay_handler(message):
            self.bank.repay_debt(message)

        @self.bot.message_handler(commands=['debt'])
        def debt_handler(message):
            self.bank.check_debt(message)
            
        @self.bot.message_handler(commands=['deposit'])
        def deposit_handler(message):
            self.bank.deposit_money(message)
        
        @self.bot.message_handler(commands=['withdraw'])
        def withdraw_handler(message):
            self.bank.withdraw_money(message)
            
        @self.bot.message_handler(commands=['amnisty'])
        def amnisty(message):
            """ Handle the /amnisty command """
            self.request_amnesty(message)
        
        @self.bot.message_handler(func=lambda message: message.from_user.id in self.amnesty_requests and self.amnesty_requests[message.from_user.id]['step'] == 1)
        def handle_amnesty_reason(message):
            """ Handle the reason part of the amnesty """
            self.collect_amnesty_reason(message)
        
        @self.bot.message_handler(func=lambda message: message.from_user.id in self.amnesty_requests and self.amnesty_requests[message.from_user.id]['step'] == 2)
        def handle_amnesty_message(message):
            """ Handle the message part of the amnesty """
            self.collect_amnesty_message(message)
            
        @self.bot.message_handler(commands=['transfer'])
        def transfer(message):
            self.bank.transfer_coins(message)
                    
        @self.bot.message_handler(func=lambda message: True)  # Catch all other messages
        def forward_to_admin(message):
            username = message.from_user.username or "Unknown"
            print("Message received: ", message.text)
            parts = message.text.split(maxsplit=1)
            if parts[0] == "кузьма" or parts[0] == "Кузьма":
                self.bot.send_message(self.admin_id, f"@{username}: {message.text}")
                
        threading.Thread(target=self.setup_schedules, daemon=True).start()