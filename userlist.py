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
    def __init__(self):
        self.list = []

    async def load_from_userlist(self, data):
        for user_data in data:
            user = User().load_from_data(user_data)
            self.list.append(user)

    async def on_user_leave(self, data):
        self.list.remove(self.get_user_by_name(data['name']))
        print('userlist length:', len(self.list))

    async def on_add_user(self, data):
        user = User().load_from_data(data)
        self.list.append(user)
        print('userlist length:', len(self.list))

    def get_user_by_name(self, name):
        for user in self.list:
            if user.name.lower() == name.lower():
                return user