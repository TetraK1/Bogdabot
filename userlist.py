import logging
logger = logging.getLogger(__name__)

class User:
    def __init__(self, name='', rank=0, muted=False, afk=False, profile_image='', profile_text=''):
        self.name = name
        self.rank = rank
        self.muted = muted
        self.afk = afk
        self.profile_image = profile_image
        self.profile_text = profile_text

    def load_from_data(self, data):
        #e.g. {'name': 'Xars', 'rank': 2, 'profile': {'image': 'https://cdn.discordapp.com/attachments/244973637508136961/618051942383484928/ls5zod7qbzj31.png', 'text': '/LOL BAZINGA XD'}, 'meta': {'afk': False, 'muted': False}}
        self.name = data['name']
        self.rank = data['rank']
        self.muted = data['meta']['muted']
        self.afk = data['meta']['afk']
        self.profile_image = data['profile']['image']
        self.profile_text = data['profile']['text']
        return self

class Userlist:
    def __init__(self, bot):
        self.bot = bot
        self.list = []
        self.bot.on('userlist', self.load_from_userlist)
        self.bot.on('userLeave', self.on_user_leave)
        self.bot.on('addUser', self.on_add_user)

    async def load_from_userlist(self, data):
        logger.debug('Loading userlist from userlist event')
        for user_data in data:
            user = User().load_from_data(user_data)
            self.list.append(user)

    async def on_user_leave(self, data):
        logger.info(data['name'] + ' left')
        self.list.remove(self.get_user_by_name(data['name']))

    async def on_add_user(self, data):
        logger.info(data['name'] + ' joined')
        user = User().load_from_data(data)
        self.list.append(user)

    def get_user_by_name(self, name):
        for user in self.list:
            if user.name.lower() == name.lower():
                return user