import asyncio
import aiosqlite
import asyncpg
import datetime as dt
import logging

logger = logging.getLogger(__name__)

class PostgresBotDB:
    def __init__(self, bot):
        self.bot = bot
        self.logger = logger
        #lock is hacky
        self.lock = asyncio.Lock()

        #used in tracking which videos are skipped
        self.current_video_id = None
        self.current_video_type = None
        self.voteskipped = False

        #Automatically register any methods named 'on_*' e.g. 'on_chatMsg'
        #to the appropriate bot event
        for attr_name in dir(self):
            split_name = attr_name.split('_', 1)
            if len(split_name) == 2 and split_name[0] == 'on':
                self.bot.on(split_name[1], getattr(self, attr_name))

    async def connect(self, user, password, database, host):
        self.logger.info('Connecting to database ' + database + '@' + host)
        self.db = await asyncpg.connect(user=user, password=password, database=database, host=host)
        self.logger.info('Connected to database')
        await self.create_tables()
        return self

    async def create_tables(self):
        async with self.lock:
            self.logger.debug('Creating tables')
            async with self.db.transaction():
                await self.db.execute(
                    """CREATE TABLE IF NOT EXISTS chat(
                        timestamp TIMESTAMP, 
                        username TEXT, 
                        msg TEXT
                    )"""
                )
                await self.db.execute(
                    """CREATE TABLE IF NOT EXISTS users(
                        username TEXT PRIMARY KEY,
                        rank TEXT
                    )"""
                )
                #type is where it's from e.g. 'yt'
                await self.db.execute(
                    """CREATE TABLE IF NOT EXISTS videos(
                        type TEXT, 
                        id TEXT,
                        duration INTERVAL, 
                        title TEXT,
                        PRIMARY KEY (type, id))"""
                )

                await self.db.execute(
                    """CREATE TABLE IF NOT EXISTS video_plays(
                        video_type TEXT,
                        video_id TEXT,
                        timestamp TIMESTAMP
                    )"""
                )

                await self.db.execute(
                    """CREATE TABLE IF NOT EXISTS usercounts(
                        timestamp TIMESTAMP,
                        usercount INTEGER
                    )"""
                )

                await self.db.execute(
                    """CREATE TABLE IF NOT EXISTS video_adds(
                        video_type TEXT,
                        video_id TEXT,
                        from_username TEXT,
                        video_uid TEXT,
                        timestamp TIMESTAMP
                    )"""
                )

                await self.db.execute(
                    """CREATE TABLE IF NOT EXISTS video_skips(
                        video_type TEXT,
                        video_id TEXT,
                        timestamp TIMESTAMP
                    )"""
                )

    async def on_chatMsg(self, data):
        if data['username'] == '[voteskip]':
            self.logger.info('Video skipped')
            self.voteskipped = True
        asyncio.create_task(self.log_chat_message(dt.datetime.fromtimestamp(data['time']/1000.0), data['username'], data['msg']))

    async def on_usercount(self, data): await self.log_usercount(data)

    async def on_changeMedia(self, data):
        #["changeMedia",{"id":"p-GVl7scrYE","title":"Great Depression Cooking - The Poorman's Meal - Higher Resolution","seconds":402,"duration":"06:42","type":"yt","meta":{},"currentTime":-3,"paused":true}]
        vtype = data['type']
        id = data['id']
        title = data['title']
        time = dt.datetime.now()
        duration = dt.timedelta(seconds=int(data['seconds']))
        if self.voteskipped and self.current_video_id is not None and self.current_video_id is not None:
            asyncio.create_task(self.log_skipped_video(self.current_video_type, self.current_video_id, time))
        self.voteskipped = False
        self.current_video_type, self.current_video_id = vtype, id
        asyncio.create_task(self.log_video_play(vtype, id, time))
        asyncio.create_task(self.log_video(vtype, id, duration, title))

    async def on_queue(self, data):
        vtype = data['item']['media']['type']
        id = data['item']['media']['id']
        duration = dt.timedelta(seconds=int(data['item']['media']['seconds']))
        title = data['item']['media']['title']
        username = data['item']['queueby']
        uid = str(data['item']['uid'])
        timestamp = dt.datetime.utcnow()
        asyncio.create_task(self.log_video(vtype, id, duration, title))
        asyncio.create_task(self.log_video_add(vtype, id, username, uid, timestamp))

    async def log_chat_message(self, time, uname, msg):
        self.logger.debug('Inserting chat message ' + str([time.strftime('%x %X'), uname, msg]))
        async with self.lock:
            async with self.db.transaction():
                await self.db.execute('INSERT INTO chat VALUES($1, $2, $3)', time, uname, msg)

    async def log_usercount(self, usercount):
        self.logger.debug('Inserting usercount ' + str(usercount))
        async with self.lock:
            async with self.db.transaction():
                await self.db.execute('INSERT INTO usercounts VALUES(CURRENT_TIMESTAMP, $1)', usercount)

    async def log_video(self, vtype, id, duration, title):
        self.logger.debug('Inserting video ' + str([vtype, id, duration, title]))
        async with self.lock:
            async with self.db.transaction():
                await self.db.execute('INSERT INTO videos VALUES($1, $2, $3, $4) ON CONFLICT DO NOTHING', vtype, id, duration, title)

    async def log_video_play(self, vtype, id, time):
        self.logger.debug('Inserting video play ' + str([vtype, id, time.strftime('%x %X')]))
        async with self.lock:
            async with self.db.transaction():
                await self.db.execute('INSERT INTO video_plays VALUES($1, $2, $3)', vtype, id, time)

    async def log_video_add(self, vtype, id, username, uid, timestamp):
        self.logger.debug('Inserting video-add ' + str([vtype, id, username]))
        async with self.lock:
            async with self.db.transaction():
                await self.db.execute('INSERT INTO video_adds VALUES($1, $2, $3, $4, $5)', vtype, id, username, uid, timestamp)

    async def log_skipped_video(self, video_type, video_id, timestamp):
        async with self.lock:
            async with self.db.transaction():
                await self.db.execute('INSERT INTO video_skips VALUES($1, $2, $3)', video_type, video_id, timestamp)
    
    async def get_quote(self, username):
        self.logger.debug('Getting quote from ' + username)
        async with self.lock:
            async with self.db.transaction():
                x = await self.db.fetch("SELECT username, msg, timestamp FROM chat WHERE username ILIKE $1 AND msg NOT LIKE '/%' AND msg NOT LIKE '$%' AND LENGTH(msg) > 20 ORDER BY RANDOM() LIMIT 1", username)
        try:
            x = x[0]
        except IndexError:
            return None

        return {'username': x['username'], 'msg': x['msg'], 'time': x['timestamp']}