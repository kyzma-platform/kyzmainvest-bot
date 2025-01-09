import time
import random

import telebot
from os import getenv

from bot.bot_replies import bot_replies

class Farm:
    def __init__(self):
        self.bot_replies = bot_replies
        self.bot = telebot.TeleBot(getenv("BOT_TOKEN"))
        self.farm_rare_coins = 50
        self.farm_rare_chance = 0.1
    
    def farm_coin(self, message, user, current_time):
        """ Farm coins for the user"""
        coins = 0
        
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
                    coins = random.randint(5, 30)
                user['coins'] += coins
                user['last_farm_time'] = current_time
                print(f"User {user['nickname']} farmed {coins} coins. Total: {user['coins']}")
                self.bot.reply_to(message, f"Вы заработали {coins} KyZmaCoin! У вас теперь {user['coins']} KyZmaCoin.")
                return user
