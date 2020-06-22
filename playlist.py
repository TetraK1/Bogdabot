import datetime as dt
import logging

class Video:
    '''{"media":{"id":"3qChRiHmbVg","title":"Four Strokes #4strokegang","seconds":155,"duration":"02:35","type":"yt","meta":{}},"uid":16239,"temp":true,"queueby":"HashiramaHasWood"}'''
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
        self.bot.socket.on('playlist', self.on_playlist)
        self.bot.socket.on('queue', self.on_queue)
        self.bot.socket.on('delete', self.on_delete)
        self.bot.socket.on('moveVide', self.on_moveVideo)
        self.logger = logging.getLogger(__name__)

    def load_from_data(self, data):
        '''Load playlist data from the "playlist" event data.
        
        Data takes the form of a list of video objects'''
        #data is from the playlist event
        #data is a list of video objects
        self.logger.info('Loading playlist')
        self.videos.clear()
        self.logger.debug('Videolist cleared')
        for video_data in data:
            self.videos.append(Video(video_data))
            self.logger.debug(f'Appended {self.videos[-1].title}')
        self.logger.info(f'Playlist has {len(self.videos)} videos')

    def get_by_uid(self, uid):
        '''Return the video object in the list matching the given uid'''
        for video in self.videos:
            if video.uid == uid:
                return video

    def on_playlist(self, data): 
        return self.load_from_data(data)

    def on_queue(self, data):
        '''{"item":{"media":{"id":"qXD9HnrNrvk","title":"Expert Wasted Entire Life Studying Anteaters","seconds":175,"duration":"02:55","type":"yt","meta":{}},"uid":16345,"temp":true,"queueby":"AsKdf"},"after":16344}'''
        new_video = Video(data=data['item'])
        after_video = self.get_by_uid(data['after'])
        video_index = self.videos.index(after_video) + 1
        self.videos.insert(video_index, new_video)
        self.logger.info(f'Video "{new_video.title}" added to {video_index}')
        self.logger.debug('Playlist is ' + str(len(self.videos)) + ' long')
    
    def on_delete(self, data):
        video = self.get_by_uid(data['uid'])
        self.videos.remove(video)
        self.logger.info(f'Video "{video.title}" deleted')
        self.logger.debug(f'Playlist is {len(self.videos)} long')

    def on_moveVideo(self, data):
        video = self.get_by_uid(data['from'])
        after_video = self.get_by_uid(data['after'])
        old_index = self.videos.index(video)
        new_index = self.videos.index(after_video) + 1
        self.videos.remove(video)
        self.videos.insert(new_index, video)
        self.logger.info(f'"{video.title}" moved from {old_index} to {new_index}')