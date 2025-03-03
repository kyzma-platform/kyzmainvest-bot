from bot.bot_replies import bot_replies
import random
import telebot
from os import getenv

class Roulette:
    def __init__(self):
        self.bot_replies = bot_replies
        self.bot = telebot.TeleBot(getenv("BOT_TOKEN"))
        self.NUMBER_PAYOUT_MULTIPLIER = 35  # Standard roulette payout for a number bet

    def roulette_game(self, message, user):
        """Simple Roulette Game with Red/Black and numbers"""

        # Validate user
        if user is None or not isinstance(user, dict) or 'coins' not in user:
            self.bot.reply_to(message, self.bot_replies['error_database'])
            return

        # Check if user has coins
        if user['coins'] <= 0:
            self.bot.send_animation(message.chat.id, 'https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExZXo5YWtjM3JxOXFhdnZ6eXgyN2s3NnR1ZzEzNXhiczQ2MWw0ODQ1ZyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/ytdPUwmGshqsJqZhET/giphy-downsized-large.gif')
            return

        # Parse the bet
        parts = message.text.split()
        if len(parts) != 3:
            self.bot.reply_to(message, "Неверный формат. Используйте: <i>/roulette ставка красный/черный/номер</i>", parse_mode="HTML")
            return

        try:
            bet_amount = int(parts[1])
        except ValueError:
            self.bot.reply_to(message, "Сумма ставки должна быть числом.")
            return

        bet_type = parts[2].lower()

        # Validate bet amount
        if bet_amount <= 0:
            self.bot.reply_to(message, "Сумма ставки должна быть больше нуля.")
            return

        if bet_amount > user['coins']:
            self.bot.reply_to(message, "У вас недостаточно монет для этой ставки.")
            return

        # Validate bet type
        if bet_type not in ["красный", "черный"] and not bet_type.isdigit():
            self.bot.reply_to(message, "Неверный тип ставки. Используйте 'красный', 'черный', или номер от 0 до 36.")
            return

        if bet_type.isdigit():
            bet_number = int(bet_type)
            if bet_number < 0 or bet_number > 36:
                self.bot.reply_to(message, "Номер ставки должен быть от 0 до 36.")
                return

        # Spin the roulette wheel
        roulette_wheel = [0] + list(range(1, 37))  # 0 (green) and numbers 1–36
        red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
        black_numbers = [2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35]

        result = random.choice(roulette_wheel)

        # Determine the result message
        if result == 0:
            result_message = "Выпал 0 (Зеленый)."
        elif result in red_numbers:
            result_message = f"Выпал номер {result} (Красный)."
        else:
            result_message = f"Выпал номер {result} (Черный)."

        # Determine if the bet is a win or a loss
        if bet_type == "красный" and result in red_numbers:
            user['coins'] += bet_amount
            win_message = f"Поздравляем! Вы выиграли {bet_amount} KyZmaCoin. Теперь у вас {user['coins']} KyZmaCoin."
        elif bet_type == "черный" and result in black_numbers:
            user['coins'] += bet_amount
            win_message = f"Поздравляем! Вы выиграли {bet_amount} KyZmaCoin. Теперь у вас {user['coins']} KyZmaCoin."
        elif bet_type.isdigit() and int(bet_type) == result:
            user['coins'] += bet_amount * self.NUMBER_PAYOUT_MULTIPLIER
            win_message = f"Поздравляем! Вы угадали число {result}. Вы выиграли {bet_amount * self.NUMBER_PAYOUT_MULTIPLIER} KyZmaCoin. Теперь у вас {user['coins']} KyZmaCoin."
        else:
            user['coins'] -= bet_amount
            win_message = f"Увы, вы проиграли {bet_amount} KyZmaCoin. Теперь у вас {user['coins']} KyZmaCoin."

        # Send the result to the user
        self.bot.reply_to(message, f"{result_message}\n{win_message}")

        return user