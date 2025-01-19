from handlers import Handlers
from admin_handler import AdminHandler

class Bot:
    def __init__(self):
        self.handlers = Handlers()
        self.bot = self.handlers.bot
        self.admin_handlers = AdminHandler(self.bot)
        
    def run_bot(self):
        self.admin_handlers.setup_admin_handler()
        self.handlers.setup_handlers()
        self.handlers.set_commands()
        self.bot.infinity_polling(skip_pending=True)
        
bot = Bot()
bot.run_bot()