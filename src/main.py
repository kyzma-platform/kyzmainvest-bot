from handlers import Handlers
from admin_handler import AdminHandler, AccessLevel
from party import Party

class Bot:
    def __init__(self):
        self.handlers = Handlers()
        self.bot = self.handlers.bot
        self.admin_handlers = AdminHandler(self.bot)
        self.party = Party(self.bot)
        
    def run_bot(self):
        self.party.setup_party_handlers()
        self.admin_handlers.setup_admin_handler()
        self.bot.add_custom_filter(AccessLevel())
        self.handlers.setup_handlers()
        self.handlers.set_commands()
        self.bot.infinity_polling(skip_pending=True)
        
bot = Bot()
bot.run_bot()