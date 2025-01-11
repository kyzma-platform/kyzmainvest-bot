import random
import time
from bot.bot_replies import bot_replies

import telebot
from os import getenv

class Slots:
    def __init__(self):
        self.bot_replies = bot_replies
        self.bot = telebot.TeleBot(getenv("BOT_TOKEN"))
        self.slot_jackpot_chance = 0.05
        self.slot_win_chance = 0.2
        
    def slot_machine(self, message, user):
        """ Simple Slot Machine Game with fruits as the results"""

        if user is None:
            self.bot.reply_to(message, self.bot_replies['error_database'])
            return

        if user['coins'] <= 0:
            self.bot.send_animation(message.chat.id, 'https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExZXo5YWtjM3JxOXFhdnZ6eXgyN2s3NnR1ZzEzNXhiczQ2MWw0ODQ1ZyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/ytdPUwmGshqsJqZhET/giphy-downsized-large.gif')
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

        self.bot.reply_to(message, message_result)
        return user