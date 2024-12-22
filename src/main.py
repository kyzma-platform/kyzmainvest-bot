from handlers import Handlers

class Bot:
    def __init__(self):
        self.handlers = Handlers()
        self.bot = self.handlers.bot
        
    def run_bot(self):
        self.handlers.setup_handlers()
        self.handlers.set_commands()
        self.bot.infinity_polling(skip_pending=True)
        
bot = Bot()
bot.run_bot()