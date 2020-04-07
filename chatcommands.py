class ChatCommand:
    def __init__(self, bot):
        #command is whatever a chat message should start with
        self.bot = bot
        self.command = ''
        self.min_rank = 1

    async def on_chat_message(self, data):
        msg = data['msg']
        name = data['username']
        args = msg.split(' ')
        if args[0].lower() != self.command.lower(): return
        if self.bot.userlist.get_user_by_name(name).rank < self.min_rank: return
        await self.trigger(args[1:])
        
    async def trigger(self, args):
        #args is a list
        pass