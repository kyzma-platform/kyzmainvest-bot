from bot.bot_commands import admin_bot_commands
from bot.bot_replies import bot_replies
from os import getenv
from database import MongoDB

class AdminHandler:
    def __init__(self, bot):
        self.bot = bot
        self.database = MongoDB()
        self.bot_commands = admin_bot_commands
        self.bot_replies = bot_replies
        self.admin_id = int(getenv("ADMIN_ID"))  # Ensure it's an integer

    def give_all_users_1000_coins(self, message):
        """Give 1000 coins to all users."""
        if message.from_user.id != self.admin_id:
            self.bot.reply_to(message, self.bot_replies['not_admin'])
            return

        users = self.database.find_users()
        chat_id = message.chat.id

        for user in users:
            updated_user = {"coins": user["coins"] + 1000}
            self.database.update_user(user["user_id"], updated_user)

        self.bot.send_message(chat_id, self.bot_replies['rozdacha'], parse_mode="HTML")

    def all_users(self, message):
        """Get all users."""
        if message.from_user.id != self.admin_id:
            self.bot.reply_to(message, self.bot_replies['not_admin'])
            return

        users = self.database.find_users()
        response_message = ""
        for index, user in enumerate(users, start=1):
            response_message += f"{index}. {user['nickname']} - {user['coins']} coins\n"
        self.bot.send_message(self.admin_id, response_message)

    def get_user(self, message):
        """Get user by nickname."""
        if message.from_user.id != self.admin_id:
            self.bot.reply_to(message, self.bot_replies['not_admin'])
            return

        parts = message.text.split()
        if len(parts) != 2:
            self.bot.reply_to(message, "Неверный формат. Используйте: /find <nickname>")
            return

        nickname = parts[1]
        user = self.database.find_user_nickname(nickname)
        if user is None:
            self.bot.reply_to(message, "Пользователь не найден.")
            return

        response_message = (
            f"Nickname: {user['nickname']}\n"
            f"ID: {user['user_id']}\n"
            f"Coins: {user['coins']}\n"
            f"Last farm time: {user['last_farm_time']}\n"
            f"Access level: {user['access_level']}\n"
            f"Debt: {user['debt']}"
        )
        self.bot.send_message(self.admin_id, response_message)

    def give_coins(self, message):
        """Give coins to a user."""
        if message.from_user.id != self.admin_id:
            self.bot.reply_to(message, self.bot_replies['not_admin'])
            return

        parts = message.text.split()
        if len(parts) != 3:
            self.bot.reply_to(message, "Неверный формат. Используйте: /give <nickname> <amount>")
            return

        try:
            nickname = parts[1]
            amount = int(parts[2])
            user = self.database.find_user_nickname(nickname)
            if user is None:
                self.bot.reply_to(message, "Пользователь не найден.")
                return

            user["coins"] += amount
            self.database.update_user(user["user_id"], user)
            self.bot.reply_to(message, f"Вы успешно дали {amount} монет пользователю {nickname}.")
        except ValueError:
            self.bot.reply_to(message, "Сумма должна быть числом.")

    def remove_coins(self, message):
        """Remove coins from a user."""
        if message.from_user.id != self.admin_id:
            self.bot.reply_to(message, self.bot_replies['not_admin'])
            return

        parts = message.text.split()
        if len(parts) != 3:
            self.bot.reply_to(message, "Неверный формат. Используйте: /remove <nickname> <amount>")
            return

        try:
            nickname = parts[1]
            amount = int(parts[2])
            user = self.database.find_user_nickname(nickname)
            if user is None:
                self.bot.reply_to(message, "Пользователь не найден.")
                return

            user["coins"] -= amount
            self.database.update_user(user["user_id"], user)
            self.bot.reply_to(message, f"Вы успешно забрали {amount} монет у пользователя {nickname}.")
        except ValueError:
            self.bot.reply_to(message, "Сумма должна быть числом.")
        
    def send_message_to_users(self, message):
        """Send a custom message to all users."""
        if message.from_user.id != self.admin_id:
            self.bot.reply_to(message, self.bot_replies['not_admin'])
            return

        parts = message.text.split(maxsplit=1)
        if len(parts) != 2:
            self.bot.reply_to(message, "Неверный формат. Используйте: /send_message <message>")
            return

        user_message = parts[1]
        users = self.database.find_users()

        for user in users:
            try:
                self.bot.send_message(user["user_id"], user_message)
            except Exception as e:
                print(f"Failed to send message to {user['nickname']}: {e}")

        self.bot.reply_to(message, "Сообщение отправлено всем пользователям.")
        
    def send_message_to_one_user(self, message):
        """Send a custom message to a specific user by nickname."""
        if message.from_user.id != self.admin_id:
            self.bot.reply_to(message, self.bot_replies['not_admin'])
            return

        parts = message.text.split(maxsplit=2)
        if len(parts) != 3:
            self.bot.reply_to(message, "Неверный формат. Используйте: /send_message_to_user <nickname> <message>")
            return

        nickname = parts[1]
        user_message = parts[2]
        user = self.database.find_user_nickname(nickname)

        if user is None:
            self.bot.reply_to(message, "Пользователь не найден.")
            return

        try:
            self.bot.send_message(user["user_id"], user_message)
            self.bot.reply_to(message, f"Сообщение отправлено пользователю {nickname}.")
        except Exception as e:
            self.bot.reply_to(message, f"Не удалось отправить сообщение пользователю {nickname}. Ошибка: {e}")

    def setup_admin_handler(self):
        @self.bot.message_handler(commands=["rozdacha"])
        def rozdacha_handler(message):
            self.give_all_users_1000_coins(message)

        @self.bot.message_handler(commands=["all"])
        def all_users_handler(message):
            self.all_users(message)

        @self.bot.message_handler(commands=["find"])
        def find_user_handler(message):
            self.get_user(message)

        @self.bot.message_handler(commands=["give"])
        def give_coins_handler(message):
            self.give_coins(message)

        @self.bot.message_handler(commands=["remove"])
        def remove_coins_handler(message):
            self.remove_coins(message)
            
        @self.bot.message_handler(commands=['send_all'])
        def send_all(message):
            self.send_message_to_users(message)
            
        @self.bot.message_handler(commands=["send"])
        def send_message_to_user_handler(message):
            self.send_message_to_one_user(message)