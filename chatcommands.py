import asyncio
import random
import datetime as dt
import logging
import re

logger = logging.getLogger('cc')

class CommandError(Exception): pass

class ChatCommands:
    def __init__(self, bot):
        self.bot = bot
        self.commands = [Roll(bot)]
        
        self.bot.socket.on('chatMsg', self.on_chat_message)
        self.cmd_pattern = re.compile(r'^%(\w*)(?: (.*?))?$')

    async def on_chat_message(self, data):
        if dt.datetime.fromtimestamp(data['time']/1000) < self.bot.start_time:
            return

        match = self.cmd_pattern.match(data['msg'])
        if not match: return

        cmd = match.group(1)
        args = []
        if match.group(2): args = match.group(2).split(' ')
        user = data['username']

        for command in self.commands:
            if cmd != command.command_name:
                continue
            asyncio.create_task(command.call(user, args))

class NoCooldownException(Exception): pass

class ChatCommand:
    command_name = 'roll' #e.g. roll
    min_rank = 3
    no_cooldown_rank = 3
    user_cooldown = dt.timedelta(minutes=1)
    global_cooldown = dt.timedelta(seconds=0)

    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger('cc.' + self.command_name)
        self.last_uses = {}
        self.last_global_use = dt.datetime(1,1,1)

    def check(self, user, args):
        if (
            self.bot.userlist[user].rank < self.min_rank
            or not dt.datetime.now() - self.last_global_use > self.global_cooldown
            or not dt.datetime.now() - self.last_uses.get(user, dt.datetime(1,1,1)) > self.user_cooldown
        ): return False

        self.logger.debug('Check passed')
        return True

    def update_cooldowns(self, user):
        if self.bot.userlist[user].rank >= self.no_cooldown_rank: return
        self.logger.debug(f'Updating cooldown for {user}')
        self.last_global_use = dt.datetime.now()
        self.last_uses[user] = dt.datetime.now()
        self.logger.debug(str(self.last_uses))

    async def call(self, user, args):
        if not self.check(user, args): return
        try:
            await self.action(user, args)
            self.update_cooldowns(user)
        except NoCooldownException:
            pass

    async def action(self, user: str, args: list[str]):
        pass

class Roll(ChatCommand):
    min_rank = 1
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

    async def action(self, user, args):
        size = 2
        try:
            size = int(args[0])
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
            msg = f'[3d]{user} rolled {self.get_names[consec]}: {result}!! [/3d] /go'
        elif random.random() < 0.01:
            msg = f'[3d]{user} rolled SINGLES: {result}!! [/3d] /feelsmeh /mehfeels'
        else:
            msg = f'{user} rolled: {result}'

        await self.bot.send_chat_message(msg)