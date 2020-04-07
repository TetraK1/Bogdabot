import random

class ChatCommand:
    command = ''
    min_rank = 1

    def __init__(self, bot):
        #command is whatever a chat message should start with
        self.bot = bot

    async def on_chat_message(self, data):
        msg = data['msg']
        name = data['username']
        args = msg.split(' ')
        if args[0].lower() != self.command.lower(): return
        if self.bot.userlist.get_user_by_name(name).rank < self.min_rank: return
        await self.trigger(data)
        
    async def trigger(self, data):
        #args is a list
        pass

class RollCommand(ChatCommand):
    command = '$roll'
    min_rank = 1
    async def trigger(self, data):
        args = data['msg'].split(' ')

        if data['username'].lower() == 'RookieMcSpooks'.lower() or data['username'].lower() == 'Gigago'.lower():
            await self.bot.send_chat_message('Fuck ' + data['username'])
            return

        size = None
        print(args)
        try:
            size = int(args[1])
        except (ValueError, IndexError): pass
        if size is None or size < 0 or size > 100: size = 2

        result = random.randint(0, 10**size - 1)
        result = str(result).zfill(size)

        rev_result = result[::-1]
        consec = 1
        for i in range(1, len(rev_result)):
            if rev_result[i-1] != rev_result[i]: break
            consec += 1

        msg = data['username'] + ' rolled: ' + result
        if consec > 1: msg = '[3d]' + msg + '[/3d]'

        await self.bot.send_chat_message(msg)