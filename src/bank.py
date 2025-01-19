import schedule
import time
from bot.bot_replies import bot_replies
import telebot
from os import getenv
from database import MongoDB

class Bank:
    def __init__(self):
        self.bot_replies = bot_replies
        self.bot = telebot.TeleBot(getenv("BOT_TOKEN"))
        self.admin_id = int(getenv("ADMIN_ID"))
        self.database = MongoDB()


    def log(self, message, user_id):
        """ Log messages to the admin in bot chat """
        user_access_level = self.database.get_access_level(user_id)
        if user_access_level == "user":
            self.bot.send_message(self.admin_id, message)

    def calculate_hourly_compound_interest(self, principal, annual_rate, hours):
        """ Calculate the compound interest applied every hour """
        n = 8760  # Number of compounding periods per year (hourly)
        t = hours / 8760  # Time in years
        amount = principal * (1 + annual_rate / n) ** (n * t)
        return amount

    def apply_interest_to_all_users(self):
        """ Apply hourly compound interest to all users' deposits """
        users = self.database.find_users()
        annual_rate = 0.05  # Example annual interest rate of 5%
        for user in users:
            if 'deposit' in user:  # Ensure the user has a deposit field
                principal = user['deposit']
                new_amount = self.calculate_hourly_compound_interest(principal, annual_rate, 1)
                user['deposit'] = new_amount
                self.database.update_user(user['user_id'], user)
                self.bot.send_message(self.admin_id, f"Interest applied to user {user['nickname']}! New deposit: {user['deposit']}")
                
    
    def deposit_money(self, message):
        """ Deposit money into the user's deposit account """
        user_id = message.from_user.id
        user = self.database.find_user_id(user_id)

        parts = message.text.split()
        if len(parts) != 2 or not parts[1].isdigit():
            self.bot.reply_to(message, "Неверный формат. Используйте: <i>/deposit количество</i>", parse_mode="HTML")
            return

        amount = int(parts[1])

        if amount <= 0:
            self.bot.reply_to(message, "Сумма депозита должна быть больше нуля.")
            return

        if user['coins'] < amount:
            self.bot.reply_to(message, "У вас недостаточно средств для депозита.")
            return

        # Deduct money from the user's coins and add to the deposit
        user['coins'] -= amount
        user['deposit'] += amount

        self.database.update_user(user_id, user)
        self.bot.reply_to(message, f"Вы успешно положили {amount} KyZmaCoin на депозит. Ваш текущий депозит: {user['deposit']} KyZmaCoin.")
        self.log(f"User @{message.from_user.username} deposited {amount} coins into their deposit", user_id)

    def withdraw_money(self, message):
        """ Withdraw money from the user's deposit account """
        user_id = message.from_user.id
        user = self.database.find_user_id(user_id)

        parts = message.text.split()
        if len(parts) != 2 or not parts[1].isdigit():
            self.bot.reply_to(message, "Неверный формат. Используйте: <i>/withdraw количество</i>", parse_mode="HTML")
            return

        amount = int(parts[1])

        if amount <= 0:
            self.bot.reply_to(message, "Сумма вывода должна быть больше нуля.")
            return

        if user['deposit'] < amount:
            self.bot.reply_to(message, "У вас недостаточно средств на депозите.")
            return

        # Deduct money from the user's deposit and add to coins
        user['deposit'] -= amount
        user['coins'] += amount

        self.database.update_user(user_id, user)
        self.bot.reply_to(message, f"Вы успешно сняли {amount} KyZmaCoin с депозита. Ваш текущий депозит: {user['deposit']} KyZmaCoin.")
        self.log(f"User @{message.from_user.username} withdrew {amount} coins from their deposit", user_id)

    def check_balance(self, message, user_id):
        """ Check the user's balance """
        user = self.database.find_user_id(user_id)
        self.bot.reply_to(message, f"Банк: {user['coins']} KyZmaCoin\nДепозит: {user['deposit']} KyZmaCoin")

    def borrow_money(self, message):
        user_id = message.from_user.id
        user = self.database.find_user_id(user_id)

        if user['debt_limit_reached']:
            self.bot.reply_to(message, "Вы исчерпали лимит долга в 1.000.000 KyZmaCoin. Пожалуйста, погасите долг, чтобы взять ещё.")
            return

        parts = message.text.split()
        if len(parts) != 2 or not parts[1].isdigit():
            self.bot.reply_to(message, "Неверный формат. Используйте: <i>/borrow количество</i>", parse_mode="HTML")
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
            self.bot.reply_to(message, "Неверный формат. Используйте: <i>/repay количество</i>")
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
        self.log(f"User {message.from_user.username} repayed debt {amount} coins.", user_id)

    def check_debt(self, message):
        user_id = message.from_user.id
        user = self.database.find_user_id(user_id)
        self.bot.reply_to(message, f"Ваш текущий долг: {user['debt']} KyZmaCoin.")
        self.log(f"User {message.from_user.username} checked their debt", user_id)

    def remind_debtors(self):
        """ Send a reminder to all users who have a debt """
        users = self.database.find_users()
        debtors = [user for user in users if user['debt'] > 0 and user['user_id'] != int(self.admin_id)]

        for debtor in debtors:
            message = f"Шановний/шановна {debtor['name']},\n\nПовідомляємо, що Ваш борг перед KyZma InVest становить {debtor['debt']} KyZmaCoin. Ми настійно просимо Вас погасити зазначену суму у найкоротші терміни. У разі неповернення боргу, ми будемо змушені вжити відповідних заходів.\n\nДля оплати боргу скористайтеся командою /repay.\n\nЗ повагою,\n\nАдміністрація KyZma InVest"
            self.bot.send_message(debtor['user_id'], message)
            self.log(f"Sent debt reminder to {debtor['nickname']}", debtor['user_id'])

    def transfer_coins(self, message):
        """ Transfer coins between users """
        sender_id = message.from_user.id
        sender = self.database.find_user_id(sender_id)

        parts = message.text.split()
        if len(parts) != 3:
            self.bot.reply_to(message, f"Неверный формат. Используйте: <i>/transfer ник монеты</i>", parse_mode="HTML")
            return

        recipient_nickname = parts[1]
        amount = int(parts[2])

        if amount <= 0:
            self.bot.reply_to(message, "Сумма перевода должна быть больше нуля.")
            return

        if sender['coins'] < amount:
            self.bot.reply_to(message, "У вас недостаточно средств для перевода.")
            return

        recipient = self.database.find_user_nickname(recipient_nickname)
        if recipient is None:
            self.bot.reply_to(message, "Пользователь не найден.")
            return

        # Deduct coins from the sender and add to the recipient
        sender['coins'] -= amount
        recipient['coins'] += amount

        self.database.update_user(sender_id, sender)
        self.database.update_user(recipient['user_id'], recipient)

        # Send confirmation messages to both users
        self.bot.reply_to(message, f"Вы успешно перевели {amount} KyZmaCoin пользователю {recipient['nickname']}.")
        self.bot.send_message(recipient['user_id'], f"Вам перевели {amount} KyZmaCoin от {sender['nickname']}.")

        # Log the transaction
        self.log(f"User {sender['nickname']} transferred {amount} coins to @{recipient['nickname']}", sender_id)
