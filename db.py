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

    async def connect(self, user, password, database, host):
        self.logger.info('Connecting to database ' + database + '@' + host)
        self.db = await asyncpg.connect(user=user, password=password, database=database, host=host)
        self.logger.info('Connected to database')
        await self.create_tables()
        return self

    async def setup_handlers(self):
        async with self.lock:
            self.bot.on('chatMsg', self.log_chat_message)
            self.bot.on('usercount', self.log_usercount)

    async def create_tables(self):
        async with self.lock:
            self.logger.debug('Creating tables')
            async with self.db.transaction():
                await self.db.execute(
                    """CREATE TABLE IF NOT EXISTS chat(
                        timestamp TIMESTAMP, 
                        username TEXT, 
                        msg TEXT)"""
                )
                await self.db.execute(
                    """CREATE TABLE IF NOT EXISTS users(
                    uname TEXT PRIMARY KEY)"""
                )
                #type is where it's from e.g. 'yt'
                await self.db.execute(
                    """CREATE TABLE IF NOT EXISTS videos(
                        type TEXT, 
                        id TEXT,
                        duration_ms INTERVAL, 
                        title TEXT,
                        PRIMARY KEY (type, id))"""
                )
                await self.db.execute(
                    """CREATE TABLE IF NOT EXISTS user_count(
                        timestamp TIMESTAMP, 
                        count INTEGER)"""
                )

    async def log_chat_message(self, data):
        self.logger.debug('Inserting chat message ' + str(data))
        time = dt.datetime.fromtimestamp(data['time']/1000.0)
        async with self.lock:
            async with self.db.transaction():
                await self.db.execute('INSERT INTO chat VALUES($1, $2, $3)', time, data['username'], data['msg'])

    async def log_usercount(self, data):
        self.logger.debug('Inserting usercount ' + str(data))
        async with self.lock:
            async with self.db.transaction():
                await self.db.execute('INSERT INTO user_count VALUES(CURRENT_TIMESTAMP, $1)', data)

    async def log_video(self, data):
        pass
    
    async def get_quote(self, username):
        self.logger.debug('Getting quote from ' + username)
        async with self.lock:
            async with self.db.transaction():
                x = await self.db.fetch("SELECT username, msg, timestamp FROM chat WHERE username ILIKE $1 ORDER BY RANDOM() LIMIT 1", username)
        try:
            x = x[0]
        except IndexError:
            return None

        return {'username': x['username'], 'msg': x['msg'], 'time': x['timestamp']}

# class SqliteBotDB:
#     def __init__(self, database):
#         self.database = database
#         self.bot.on('chatMsg', self.log_chat_message)

#     async def connect(self):
#         self.db = await aiosqlite.connect(self.database)
#         await self.create_tables()

#     async def create_tables(self):
#         await self.db.execute('CREATE TABLE IF NOT EXISTS chat(timestamp INTEGER, username TEXT, msg TEXT)')
#         await self.db.execute('CREATE TABLE IF NOT EXISTS users(uname TEXT)')
#         #type is where it's from e.g. 'yt'
#         await self.db.execute('CREATE TABLE IF NOT EXISTS videos(type TEXT, id TEXT, duration_ms INTEGER, title TEXT, PRIMARY KEY (type, id))')
#         await self.db.execute('CREATE TABLE IF NOT EXISTS user_count(timestamp INTEGER, count INTEGER)')
#         await self.db.commit()

#     async def log_chat_message(self, data):
#         data = (data['time'], data['username'], data['msg'])
#         await self.db.execute('INSERT INTO chat VALUES(?, ?, ?)', data)
#         await self.db.commit()

#     async def log_usercount(self, data):
#         data = data,
#         await self.db.execute('INSERT INTO user_count VALUES(CURRENT_TIMESTAMP, ?)', data)
#         await self.db.commit()

#     async def log_video(self, data):
#         pass
    
#     async def get_quote(self, username):
#         x = await self.db.execute("SELECT username, msg, timestamp FROM chat WHERE username = ? COLLATE NOCASE ORDER BY RANDOM() LIMIT 1", (username,))
#         x = await x.fetchall()
#         try:
#             x = x[0]
#         except IndexError:
#             return None
#         return {'username': x[0], 'msg': x[1], 'time': dt.datetime.fromtimestamp(x[2] / 1000)}