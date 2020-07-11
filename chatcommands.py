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
            c = cc.on_chat_message
            if asyncio.iscoroutine(c) or asyncio.iscoroutinefunction(c):
                asyncio.create_task(c(data))
            else:
                asyncio.get_running_loop().call_soon(c, data)

    def get_command(self, command_name):
        for cc in self.commands:
            if cc.command_name == command_name:
                return cc

class ChatCommand:
    command_name = '' #e.g. $roll
    min_rank = 3
    user_cooldown = dt.timedelta(minutes=1)
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
    min_rank = 3
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
    min_rank = 3
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

def adjust_karma(bot, user, adjustment):
    if 'cc' not in bot.state: bot.state['cc'] = {}
    if 'karma' not in bot.state['cc']: bot.state['cc']['karma'] = {}
    karmas = bot.state['cc']['karma']
    user = user.lower()
    if user.lower() not in karmas:
        karmas[user.lower()] = 0
    karmas[user.lower()] += adjustment
    #this is blocking the event loop and probably needs to get changed
    bot.write_state()

def get_karma(bot, user):
    return bot.state['cc']['karma'][user.lower()]

class Upvote(ChatCommand):
    command_name = '$upvote' #e.g. $roll
    min_rank = 1
    user_cooldown = dt.timedelta(seconds=60)
    global_cooldown = dt.timedelta(seconds=0)

    async def command(self, data):
        args = data['msg'].split(' ')

        try: user = args[1]
        except IndexError: return False

        if user.lower() == data['username'].lower():
            await self.bot.send_chat_message("You can't upvote yourself.")
            return False

        adjust_karma(self.bot, user, 1)
        karma = get_karma(self.bot, user)
        await self.bot.send_chat_message(f"{user} has {karma} karma.")
        return True


class Downvote(ChatCommand):
    command_name = '$downvote' #e.g. $roll
    min_rank = 1
    user_cooldown = dt.timedelta(seconds=60)
    global_cooldown = dt.timedelta(seconds=0)

    async def command(self, data):
        args = data['msg'].split(' ')

        try: user = args[1]
        except IndexError: return False

        adjust_karma(self.bot, user, -1)
        karma = get_karma(self.bot, user)
        await self.bot.send_chat_message(f"{user} has {karma} karma.")
        return True

class GetKarma(ChatCommand):
    command_name = '$karma' #e.g. $roll
    min_rank = 1
    user_cooldown = dt.timedelta(seconds=60)
    global_cooldown = dt.timedelta(seconds=0)

    async def command(self, data):
        args = data['msg'].split(' ')

        try: user = args[1]
        except IndexError: return False

        try: karma = get_karma(self.bot, user)
        except KeyError: return False
        print(type(karma))
        await self.bot.send_chat_message(f"{user} has {karma} karma.")
        return True

class SetKarma(ChatCommand):
    command_name = '$setkarma' #e.g. $roll
    min_rank = 3
    user_cooldown = dt.timedelta(seconds=0)
    global_cooldown = dt.timedelta(seconds=0)

    async def command(self, data):
        args = data['msg'].split(' ')

        try: user = args[1]
        except IndexError: return False

        try: karma = get_karma(self.bot, user)
        except KeyError: karma = 0

        adjust_karma(self.bot, user,  int(args[2]) - karma)
        karma = get_karma(self.bot, user)
        await self.bot.send_chat_message(f"{user} has {karma} karma.")
        return True

class SetRank(ChatCommand):
    command_name = '$setrank' #e.g. $roll
    min_rank = 3
    user_cooldown = dt.timedelta(minutes=0)
    global_cooldown = dt.timedelta(seconds=0)
    
    async def command(self, data):
        args = data['msg'].split(' ')

        if len(args) < 3: return False

        command = self.bot.chat_commands.get_command(args[1])
        if command is None: return False
        
        try: rank = int(args[2])
        except ValueError: return False

        command.min_rank = rank
        logger.info(f'{command.command_name} set to rank {rank}')
        asyncio.create_task(self.bot.send_chat_message(f'{command.command_name} set to rank {rank}'))
        return True