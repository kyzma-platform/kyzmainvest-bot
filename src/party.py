from database import MongoDB
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

class Party:
    def __init__(self, bot):
        self.database = MongoDB()
        self.bot = bot
        
    def create_party(self, party_name, party_creator):
        """ Create party in the database """
        return self.database.add_party(party_name, party_creator)
    
    def invite_to_party(self, user_id, inviter_id):
        """ Отправляет приглашение в партию """
        party = self.database.find_party_id(inviter_id)  # Ищем партию по ID владельца
        
        if not party:
            return "❌ Вы не являетесь владельцем ни одной партии!"
        
        if user_id in party["party_members"]:
            return "❌ Этот пользователь уже в вашей партии!"
        
        # Создаём inline-клавиатуру
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("✅ Принять", callback_data=f"accept_invite:{party['party_name']}:{user_id}"),
            InlineKeyboardButton("❌ Отклонить", callback_data="decline_invite")
        )
        
        # Отправляем приглашение пользователю
        self.bot.send_message(
            user_id,
            f"📩 Вас пригласили в партию {party['party_name']}!\nПринять приглашение?",
            reply_markup=keyboard,
        )
        return f"✅ Приглашение в партию {party['party_name']} отправлено пользователю {user_id}!"
    
    def accept_invitation(self, party_name, user_id):
        """ Принимает приглашение и добавляет пользователя в партию """
        return self.database.add_party_member(party_name, user_id)
    
    def remove_party_member(self, party_name, user_id):
        """ Remove user from the party """
        return self.database.remove_party_member(party_name, user_id)
    
    def get_party(self, party_name, message):
        """ Get party by name """
        party = self.database.find_party_name(party_name)
        party_creator = party.get("party_creator")
        party_creator = self.database.find_user_id(party_creator)
        message_bot = f"Партия {party_name}:\nВладелец: {party_creator['nickname']}\nУчастники: {party['party_members']}\nГречка: {party['grechka']} кг"
        self.bot.reply_to(message, message_bot)
    
    def buy_grechka(self, party_creator_id, amount):
        party = self.database.find_party_id(party_creator_id)
        if not party:
            return "❌ Вы не являетесь владельцем ни одной партии!"
        if amount <= 0:
            return "❌ Количество гречки должно быть положительным числом!"
        
        cost = amount * 30
        
        user = self.database.find_user_id(party_creator_id)
        if not user:
            return "❌ Пользователь не найден!"
        
        user_coins = user.get("coins", 0)
        
        if user_coins < cost:
            return f"❌ У вас недостаточно монет для покупки {amount} кг гречки! Требуется {cost} монет, а у вас только {user_coins} монет."
        
        current_grechka = party.get("grechka", 0)
        new_grechka = current_grechka + amount
        self.database.update_party(party["party_name"], grechka=new_grechka)
        
        new_user_coins = user_coins - cost
        self.database.update_user(party_creator_id, {"coins": new_user_coins})
        
        return f"✅ Вы успешно купили {amount} кг гречки для партии {party['party_name']}! Всего в партии теперь {new_grechka} кг. Ваш новый баланс: {new_user_coins} монет."
    
    def distribute_grechka_to_all(self, party_creator_id, amount_per_user):
        """ Раздаёт гречку всем пользователям с указанием количества на каждого """
        if amount_per_user <= 0:
            return "❌ Количество гречки должно быть положительным числом!"
        
        # Проверяем, является ли пользователь владельцем партии
        party = self.database.find_party_id(party_creator_id)
        if not party:
            return "❌ Вы не являетесь владельцем ни одной партии!"
        
        current_party_grechka = party.get("grechka", 0)
        
        # Получаем всех пользователей
        users = self.database.find_users()
        total_users = len(users)
        
        # Проверяем, хватает ли гречки на всех пользователей
        required_grechka = amount_per_user * total_users
        
        if current_party_grechka < required_grechka:
            return f"❌ У вас недостаточно гречки для раздачи по {amount_per_user} кг каждому пользователю! У вас всего {current_party_grechka} кг, а для всех пользователей нужно {required_grechka} кг."
        
        # Раздаем гречку всем пользователям
        for user in users:
            user_id = user["user_id"]
            current_grechka = user.get("grechka", 0)
            new_grechka = current_grechka + amount_per_user
            
            # Обновляем количество гречки у пользователя
            self.database.update_user(user_id, {"grechka": new_grechka})
        
        # Уменьшаем гречку у владельца партии
        new_party_grechka = current_party_grechka - required_grechka
        self.database.update_party(party["party_name"], grechka=new_party_grechka)
        
        return f"✅ Раздано {required_grechka} кг гречки всем пользователям! Каждый пользователь получил по {amount_per_user} кг. У владельца партии теперь {new_party_grechka} кг."
        
    def setup_party_handlers(self):
        @self.bot.message_handler(func=lambda message: message.text.lower().startswith("!создать"))
        def create_party_handler(message):
            parts = message.text.split(maxsplit=1)  # Разбиваем по первому пробелу
            if len(parts) != 2:
                return self.bot.reply_to(message, "❌ Используйте: !создать <название_партии>")
            
            party_name = parts[1]  # Берём всё, что идёт после "!создать"
            party_creator = message.from_user.id
            print(party_name)
            
            # Проверяем, есть ли у пользователя уже партия
            existing_party = self.database.find_party_id(party_creator)
            if existing_party:
                return self.bot.reply_to(message, "❌ Вы уже являетесь владельцем другой партии!")

            result = self.create_party(party_name, party_creator)
            self.bot.reply_to(message, result)
            
        @self.bot.message_handler(func=lambda message: message.reply_to_message and message.text.lower() == "!пригласить")
        def invite_reply_handler(message):
            """ Обработчик приглашения в партию (ответом на сообщение) """
            replied_user_id = message.reply_to_message.from_user.id  # ID приглашённого
            inviter_id = message.from_user.id  # ID приглашающего (должен быть владельцем партии)
            
            result = self.invite_to_party(replied_user_id, inviter_id)
            self.bot.reply_to(message, result)
        
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith("accept_invite"))
        def accept_invite_handler(call):
            """ Обработчик нажатия кнопки "Принять" в приглашении """
            _, party_name, user_id = call.data.split(":")
            user_id = int(user_id)
            
            if call.from_user.id != user_id:
                return self.bot.answer_callback_query(call.id, "❌ Это приглашение не для вас!")

            result = self.accept_invitation(party_name, user_id)
            self.bot.edit_message_text(
                f"🎉 Вы успешно вступили в партию **{party_name}**!",
                call.message.chat.id, call.message.message_id,
                parse_mode="Markdown"
            )
            self.bot.answer_callback_query(call.id, result)
        
        @self.bot.callback_query_handler(func=lambda call: call.data == "decline_invite")
        def decline_invite_handler(call):
            """ Обработчик нажатия кнопки "Отклонить" в приглашении """
            self.bot.edit_message_text("❌ Вы отклонили приглашение в партию.", call.message.chat.id, call.message.message_id)
            self.bot.answer_callback_query(call.id, "Приглашение отклонено.")
            
        @self.bot.message_handler(func=lambda message: message.reply_to_message and message.text.lower() == "!выгнать")
        def remove_party_member_reply_handler(message):
            replied_user_id = message.reply_to_message.from_user.id
            party_creator_id = message.from_user.id
            
            party = self.database.find_party_id(party_creator_id)
            if not party:
                return self.bot.reply_to(message, "❌ Вы не являетесь владельцем ни одной партии.")
            
            party_name = party["party_name"]
            result = self.remove_party_member(party_name, replied_user_id)
            self.bot.reply_to(message, result)
        
        @self.bot.message_handler(func=lambda message: message.text.lower().startswith("!найти"))
        def get_party_handler(message):
            parts = message.text.split(maxsplit=1)  # Разделяем сообщение
            if len(parts) != 2:
                return self.bot.reply_to(message, "❌ Используйте: !партия <название_партии>")

            party_name = parts[1]  # Берём всё, что идёт после "!партия"
            self.get_party(party_name, message)
            
        @self.bot.message_handler(func=lambda message: message.text.lower().startswith("!гречка купить"))
        def buy_grechka_handler(message):
            parts = message.text.split(maxsplit=2)
            if len(parts) != 3:
                return self.bot.reply_to(message, "❌ Используйте: !гречка купить <количество>")

            try:
                amount = int(parts[2])
            except ValueError:
                return self.bot.reply_to(message, "❌ Количество гречки должно быть числом!")

            party_creator_id = message.from_user.id
            result = self.buy_grechka(party_creator_id, amount)
            self.bot.reply_to(message, result)
            
        @self.bot.message_handler(func=lambda message: message.text.lower().startswith("!гречка раздать"))
        def distribute_grechka_handler(message):
            """ Обработчик для раздачи гречки всем пользователям """
            parts = message.text.split(maxsplit=2)
            if len(parts) != 3:
                return self.bot.reply_to(message, "❌ Используйте: !раздать гречку всем <количество_на_пользователя>")

            try:
                amount_per_user = int(parts[2])
            except ValueError:
                return self.bot.reply_to(message, "❌ Количество гречки должно быть числом!")

            party_creator_id = message.from_user.id
            result = self.distribute_grechka_to_all(party_creator_id, amount_per_user)
            self.bot.reply_to(message, result)
                
        print("✅ Party handlers are ready")