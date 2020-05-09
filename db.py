import asyncio
import aiosqlite
import asyncpg
import datetime as dt
import logging
import types
import json

logger = logging.getLogger(__name__)

class PostgresBotDB:
    def __init__(self, bot):
        self.bot = bot
        self.logger = logger
        #lock is hacky
        self.lock = asyncio.Lock()

        #used in tracking which videos are skipped
        #important to note there may be data race issues
        self.current_video_id = None
        self.current_video_type = None
        self.voteskipped = False

        #Automatically register any methods named 'on_*' e.g. 'on_chatMsg'
        #to the appropriate bot event
        for attr_name in dir(self):
            split_name = attr_name.split('_', 1)
            if len(split_name) == 2 and split_name[0] == 'on':
                self.bot.on(split_name[1], getattr(self, attr_name))
        self.patch_trigger()

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
                with open('queries/setup.sql') as f: query = f.read()
                await self.db.execute(query)

    async def log_event(self, timestamp, event, data):
        self.logger.debug('Logging event ' + str(event) + ': ' + str(data))
        data = json.dumps(data)
        async with self.lock:
            async with self.db.transaction():
                await self.db.execute('INSERT INTO events VALUES($1, $2, $3)', timestamp, event, data)

    def patch_trigger(self):
        """Place a hook in the bot's socket's trigger_event
        
        Full of garbage patching, need to fix"""
        bot_te = self.bot.socket._trigger_event
        async def _trigger_event(bot_self, event, namespace, *args):
            try:
                asyncio.create_task(self.log_event(dt.datetime.now(), event, args[0]))
            except IndexError: pass #connect event args are an empty tuple
            await bot_te(event, namespace, *args)
        self.bot.socket._trigger_event = types.MethodType(_trigger_event, self.bot.socket)
