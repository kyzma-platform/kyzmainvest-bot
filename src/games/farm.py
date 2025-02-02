import time
import random

import telebot
from os import getenv

from bot.bot_replies import bot_replies

from database import MongoDB

class Farm:
    def __init__(self):
        self.bot_replies = bot_replies
        self.bot = telebot.TeleBot(getenv("BOT_TOKEN"))
        self.database = MongoDB()
        self.budget = 5587251063
        self.owner = getenv("ADMIN_ID")
        self.farm_rare_coins = 600
        self.farm_rare_chance = 0.1
        self.tax = 0.4
    
    def farm_coin(self, message, user, current_time):
        """ Farm coins for the user"""
        coins = 0
        coins_tax = 0
        coins_after_tax = 0
        
        if user is None:
            self.bot.reply_to(message, self.bot_replies['error_database'])
        else:
            if current_time - user['last_farm_time'] < 3600:
                remaining_time = 3600 - (current_time - user['last_farm_time'])
                remaining_minutes = remaining_time // 60
                remaining_seconds = remaining_time % 60
                self.bot.reply_to(message, f"Вы можете фармить снова через {int(remaining_minutes)} минут и {int(remaining_seconds)} секунд.")
            else:
                if random.random() < self.farm_rare_chance:
                    coins = self.farm_rare_coins
                else:
                    coins = random.randint(40, 480)
                    coins_tax = round(coins * self.tax)
                    coins_after_tax = coins - coins_tax
                print(coins_after_tax)
                budget = self.database.find_user_id(self.budget)
                budget['coins'] += coins_tax
                user['coins'] += coins_after_tax
                user['last_farm_time'] = current_time
                print(f"User {user['nickname']} farmed {coins} coins. Total: {user['coins']}")
                self.bot.reply_to(message,
                    f"Вы заработали {coins} KyZmaCoin\n"
                    f"Налог: {coins_tax} KyZmaCoin\n"
                    f"Зарплата после налога: {coins_after_tax} KyZmaCoin\n" 
                    f"Итоговая сумма: {user['coins']} KyZmaCoin\n"
                    f"Вы сможете снова фармить через 1 час")
                self.bot.send_message(self.owner, f"{coins_tax} added to budget.\n Budget:{budget['coins']}")
                return user
