import asyncio
import random
import datetime as dt
import logging

logger = logging.getLogger('cc')

class ChatCommands:
    def __init__(self, bot):
        self.bot = bot
        self.commands = [cc(self.bot) for cc in ChatCommand.__subclasses__()]
        self.bot.socket.on('chatMsg', self.on_chat_message)

    async def on_chat_message(self, data):
        if dt.datetime.fromtimestamp(data['time']/1000) < self.bot.start_time:
            return
        for cc in self.commands:
            asyncio.create_task(cc(data))

class ChatCommand:
    command_name = '' #e.g. $roll
    min_rank = 3
    user_cooldown = dt.timedelta(minutes=3)
    global_cooldown = dt.timedelta(seconds=0)

    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger('cc.' + self.command_name)
        self.last_uses = {}
        self.last_global_use = dt.datetime(1,1,1)

    async def __call__(self, *args, **kwargs): return await self.on_chat_message(*args, **kwargs)

    async def on_chat_message(self, data):
        if not self.check(data): return
        if await self.command(data):
            self.update_cooldowns(data)

    def check(self, data):
        '''Check if command should be triggered by chatMsg data.

        Checks if the msg is to call this command, if the user has high enough
        rank, if the command is off global cooldown, and finally if off
        cooldown for the specific user.
        '''
        msg = data['msg']
        name = data['username']
        args = msg.split(' ')
        if (
            args[0].lower() != self.command_name.lower()
            or self.bot.userlist[name].rank < self.min_rank
            or not dt.datetime.now() - self.last_global_use > self.global_cooldown
            or not dt.datetime.now() - self.last_uses.get(name, dt.datetime(1,1,1)) > self.user_cooldown
        ): return False
        self.logger.debug('Check passed')
        return True

    def update_cooldowns(self, data):
        self.logger.debug(f'Updating cooldown for {data["username"]}')
        name = data['username']
        self.last_global_use = dt.datetime.now()
        self.last_uses[name] = dt.datetime.now()
        self.logger.debug(str(self.last_uses))

    async def command(self, data):
        #should return true or false, indicating whether cooldown should be triggered
        return True

class QuoteCommand(ChatCommand):
    command_name = '$quote' #e.g. $roll
    min_rank = 2
    user_cooldown = dt.timedelta(seconds=60)
    global_cooldown = dt.timedelta(seconds=0)

    async def command(self, data):
        if self.bot.db is None:
            await self.bot.send_chat_message('Database not connected')
            return True
        try:
            name = data['msg'].split(' ')[1]
        except IndexError: return False
        quote = await self.bot.db.get_quote(name)
        if quote is None: return False
        q_name, q_time, q_msg = quote['username'], quote['time'], quote['msg']
        q_time = q_time.strftime('%a %b %d %Y')
        quote = f'[{q_name} {q_time}] {q_msg}'
        await self.bot.send_chat_message(quote)
        return True

class RollCommand(ChatCommand):
    command_name = '$roll' #e.g. $roll
    min_rank = 1
    user_cooldown = dt.timedelta(seconds=60)
    global_cooldown = dt.timedelta(seconds=0)

    get_names = {
        2: 'DUBS',
        3: 'TRIPS',
        4: 'QUADS',
        5: 'QUINTS',
        6: 'SEXTS',
        7: 'SEPTS',
        8: 'OCTS',
        9: 'NOCTS',
        10: 'DECS',
    }

    async def command(self, data):
        args = data['msg'].split(' ')

        size = 2
        try:
            size = int(args[1])
        except (ValueError, IndexError):
            pass
        size = min(max(1, size), 10)

        result = random.randint(0, 10**size - 1)
        result = str(result).zfill(size)

        consec = 1
        digit = result[-1]
        for i in result[:-1][::-1]: #cut off last digit then reverse
            if i != digit: break
            else: consec += 1

        if consec > 1: 
            msg = f'[3d]{data["username"]} rolled {self.get_names[consec]}: {result}!! [/3d] /go'
        elif random.random() < 0.01:
            msg = f'[3d]{data["username"]} rolled SINGLES: {result}!! [/3d] /feelsmeh /mehfeels'
        else:
            msg = f'{data["username"]} rolled: {result}'

        await self.bot.send_chat_message(msg)
        return True