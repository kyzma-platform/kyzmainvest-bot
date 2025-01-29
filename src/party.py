from database import MongoDB

class Party:
    def __init__(self, bot):
        self.database = MongoDB()
        self.bot = bot
        self.setup_party_handlers()
        
        
    def create_party(self, party_name, party_creator):
        """ Create party in the database """
        return self.database.add_party(party_name, party_creator)
    
    def add_party_member(self, party_name, user_id):
        """ Add user to the party """
        return self.database.add_party_member(party_name, user_id)
    
    def get_party(self, party_name):
        """ Get party by name """
        return self.database.find_party(party_name=party_name)
    
    def get_party_members(self, party_name):
        """ Get party members by party name """
        party = self.get_party(party_name)
        return party['party_members'] if party else None
        
    def get_party_creator(self, party_name):
        """ Get party creator by party name """
        party = self.get_party(party_name)
        return party['party_creator'] if party else None
        
    def setup_party_handlers(self):
        @self.bot.message_handler(commands=['create_party'])
        def create_party_handler(message):
            parts = message.text.split(maxsplit=1)
            if len(parts) != 2:
                self.bot.reply_to(message, "Неверный формат. Используйте: /create_party <party_name>")
                return
            party_name = parts[1]
            party_creator = message.from_user.id
            self.bot.reply_to(message, self.create_party(party_name, party_creator))
            
        @self.bot.message_handler(commands=['add_party_member'])
        def add_party_member_handler(message):
            parts = message.text.split(maxsplit=2)
            if len(parts) != 3:
                self.bot.reply_to(message, "Неверный формат. Используйте: /add_party_member <party_name> <user_id>")
                return
            party_name = parts[1]
            user_id = parts[2]
            self.bot.reply_to(message, self.add_party_member(party_name, user_id))
            
        @self.bot.message_handler(commands=['get_party'])
        def get_party_handler(message):
            parts = message.text.split(maxsplit=1)
            if len(parts) != 2:
                self.bot.reply_to(message, "Неверный формат. Используйте: /get_party <party_name>")
                return
            party_name = parts[1]
            party = self.get_party(party_name)
            self.bot.reply_to(message, f"Party {party_name}: {party}" if party else f"Party {party_name} not found")
                
        @self.bot.message_handler(commands=['get_party_members'])
        def get_party_members_handler(message):
            parts = message.text.split(maxsplit=1)
            if len(parts) != 2:
                self.bot.reply_to(message, "Неверный формат. Используйте: /get_party_members <party_name>")
                return
            party_name = parts[1]
            party_members = self.get_party_members(party_name)
            self.bot.reply_to(message, f"Party {party_name} members: {party_members}" if party_members else f"Party {party_name} not found")
                
        @self.bot.message_handler(commands=['get_party_creator'])
        def get_party_creator_handler(message):
            parts = message.text.split(maxsplit=1)
            if len(parts) != 2:
                self.bot.reply_to(message, "Неверный формат. Используйте: /get_party_creator <party_name>")
                return
            party_name = parts[1]
            party_creator = self.get_party_creator(party_name)
            self.bot.reply_to(message, f"Party {party_name} creator: {party_creator}" if party_creator else f"Party {party_name} not found")
                
        print("Party handlers are ready")
        
    