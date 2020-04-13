import datetime as dt
import logging

class Video:
    #example json
    """
    {
        'media': {
            'id': '3qChRiHmbVg',
            'title': 'Four Strokes #4strokegang',
            'seconds': 155,
            'duration': '02:35',
            'type': 'yt',
            'meta': {}
        },
        'uid': 16239,
        'temp': True,
        'queueby': 'HashiramaHasWood'
    }
    """
    def __init__(self, data=None):
        if data is not None: self.load_from_data(data)

    def load_from_data(self, data):
        self.id = data['media']['id']
        self.title = data['media']['title']
        self.seconds = dt.timedelta(seconds=data['media']['seconds'])
        self.duration = data['media']['duration']
        self.type = data['media']['type']
        self.meta = data['media']['meta']
        self.uid = data['uid']
        self.temp = data['temp']
        self.queueby = data['queueby']

class Playlist:
    def __init__(self, bot):
        self.videos = []
        self.bot = bot
        self.bot.on('playlist', self.on_playlist)
        self.bot.on('queue', self.on_queue)
        self.bot.on('delete', self.on_delete)
        self.logger = logging.getLogger(__name__)

    async def load_from_data(self, data):
        self.videos.clear()
        for video_data in data:
            self.videos.append(Video(video_data))
        self.logger.debug('Loaded playlist, ' + str(len(self.videos)) + ' videos long')

    def get_by_uid(self, uid):
        for video in self.videos:
            if video.uid == uid:
                return video

    def insert_after_uid(self, uid, video):
        after_index = self.videos.index(self.get_by_uid(uid))
        self.videos.insert(after_index + 1, video)

    async def on_playlist(self, data): return await self.load_from_data(data)

    async def on_queue(self, data):
        after_video = self.get_by_uid(data['after'])
        new_video = Video(data=data['item'])
        self.logger.debug(f'Inserting video "{new_video.title}" after "{after_video.title}"')
        self.insert_after_uid(data['after'], new_video)
        self.logger.debug('Playlist is ' + str(len(self.videos)) + ' long')
    
    async def on_delete(self, data):
        video = self.get_by_uid(data['uid'])
        self.logger.debug(f'Removing video "{video.title}"')
        self.videos.remove(video)
        self.logger.debug(f'Playlist is {len(self.videos)} long')
        return

    async def on_moveVideo(self, data):
        video = self.get_by_uid(data['from'])
        self.logger.debug(f'Moving video "{video.title}"')
        self.videos.remove(video)
        self.insert_after_uid(data['after'], video)