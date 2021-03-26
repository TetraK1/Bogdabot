import asyncio
import random
import datetime as dt
import logging
import re

logger = logging.getLogger('cc')

class CommandError(Exception): pass

kc = None

class ChatCommands:
    def __init__(self, bot):
        self.bot = bot
        self.commands = [
            Roll(bot),
            Upvote(bot),
            Downvote(bot),
            GetKarma(bot),
        ]
        
        self.bot.socket.on('chatMsg', self.on_chat_message)
        self.cmd_pattern = re.compile(r'^%(\w*)(?: (.*?))?$')

        global kc
        kc = KarmaController(bot)

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
    command_name = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa' #e.g. roll
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
        if self.bot.userlist[user].rank < self.min_rank: return False
        if self.bot.userlist[user].rank < self.no_cooldown_rank:
            if (
                dt.datetime.now() - self.last_global_use < self.global_cooldown 
                or dt.datetime.now() - self.last_uses.get(user, dt.datetime(1,1,1)) < self.user_cooldown
            ): return False

        self.logger.debug('Check passed')
        return True

    def update_cooldowns(self, user):
        self.logger.debug(f'Updating cooldown for {user}')
        self.last_global_use = dt.datetime.now()
        self.last_uses[user] = dt.datetime.now()
        self.logger.debug(str(self.last_uses))

    async def call(self, user: str, args: list[str]):
        if not self.check(user, args): return
        try:
            await self.action(user, args)
            self.update_cooldowns(user)
        except NoCooldownException:
            pass

    async def action(self, user: str, args: list[str]):
        pass

class Roll(ChatCommand):
    command_name = 'roll'
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
        elif random.random() < 0.1:
            msg = f'[3d]{user} rolled SINGLES: {result}!! [/3d] /feelsmeh /mehfeels'
        else:
            msg = f'{user} rolled: {result}'

        await self.bot.send_chat_message(msg)


class KarmaController:
    def __init__(self, bot):
        self.bot = bot
        self.karma = {}
        self.load()

    def load(self):
        try: cc = self.bot.state['cc']
        except KeyError: self.bot.state['cc'] = {}
        try: karma = cc['karma']
        except KeyError: self.bot.state['cc']['karma'] = {}
        self.bot.write_state()
        return self.bot.state['cc']['karma']

    def save(self):
        self.bot.state['cc']['karma'] = self.karma
        self.bot.write_state()

    def get_user_votes(self, name: str):
        if name not in self.karma:
            self.karma[name] = {}
        return self.karma[name]

    def get_user_vote(self, target_name, agent_name):
        votes = self.get_user_votes(target_name)
        return votes[agent_name]

    def get_user_karma(self, name):
        votes = self.get_user_votes(name)
        karma_value = sum((1 if vote else -1) for vote in votes.values())
        return karma_value

    def set_vote(self, vote: bool, agent_name, target_name):
        if target_name not in self.karma: self.karma[target_name] = {}
        self.karma[target_name][agent_name] = vote
        self.save()

class Upvote(ChatCommand):
    command_name = 'upvote'
    min_rank = 1

    async def action(self, user, args):
        try: target_name = self.bot.userlist[args[0]].name
        except KeyError:
            await self.bot.send_chat_message("That user is not online")
            raise NoCooldownException()
        try:
            if kc.get_user_vote(target_name, user) == True:
                await self.bot.send_chat_message("You've already upvoted that user.")
                raise NoCooldownException()
        except KeyError: pass

        kc.set_vote(True, user, target_name)
        new_karma = kc.get_user_karma(target_name)
        await self.bot.send_chat_message(f"{user} upvoted {target_name}, who now has {new_karma} karma")

class Downvote(ChatCommand):
    command_name = 'downvote'
    min_rank = 1

    async def action(self, user, args):
        try: target_name = self.bot.userlist[args[0]].name
        except KeyError:
            await self.bot.send_chat_message("That user is not online")
            raise NoCooldownException()

        try:
            if kc.get_user_vote(target_name, user) == False:
                await self.bot.send_chat_message("You've already downvoted that user.")
                raise NoCooldownException()
        except KeyError: pass

        kc.set_vote(False, user, target_name)
        new_karma = kc.get_user_karma(target_name)
        await self.bot.send_chat_message(f"{user} downvoted {target_name}, who now has {new_karma} karma")

class GetKarma(ChatCommand):
    command_name = 'karma'
    min_rank = 1

    async def action(self, user, args):
        if len(args) == 0:
            name = user
        else:
            try:
                name = self.bot.userlist[args[0]].name
            except KeyError:
                await self.bot.send_chat_message("That user is not online.")
                raise NoCooldownException()
        
        user_karma = kc.get_user_karma(name)
        await self.bot.send_chat_message(f"{name} has {user_karma} karma.")
    

