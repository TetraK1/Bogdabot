import logging
logger = logging.getLogger(__name__)

class User:
    @classmethod
    def create_from_data(cls, data):
        #e.g. {'name': 'Xars', 'rank': 2, 'profile': {'image': 'https://cdn.discordapp.com/attachments/244973637508136961/618051942383484928/ls5zod7qbzj31.png', 'text': '/LOL BAZINGA XD'}, 'meta': {'afk': False, 'muted': False}}
        return cls(
            name = data['name'],
            rank = data['rank'],
            muted = data['meta']['muted'],
            afk = data['meta']['afk'],
            profile_image = data['profile']['image'],
            profile_text = data['profile']['text'] 
        )

    def __init__(self, name='', rank=0, muted=False, afk=False, profile_image='', profile_text=''):
        self.name = name
        self.rank = rank
        self.muted = muted
        self.afk = afk
        self.profile_image = profile_image
        self.profile_text = profile_text

class Userlist:
    def __init__(self, bot):
        self.bot = bot
        self.users = {}
        self.bot.socket.on('userlist', self.load_from_userlist)
        self.bot.socket.on('userLeave', self.on_user_leave)
        self.bot.socket.on('addUser', self.on_add_user)

    def __getitem__(self, key): return self.users[key]

    async def load_from_userlist(self, data):
        logger.info('Loading userlist')
        for user_data in data:
            user = User.create_from_data(user_data)
            self.users[user.name] = user

    async def on_user_leave(self, data):
        logger.info(data['name'] + ' left')
        del self.users[data['name']]

    async def on_add_user(self, data):
        logger.info(data['name'] + ' joined')
        user = User.create_from_data(data)
        self.users[user.name] = user