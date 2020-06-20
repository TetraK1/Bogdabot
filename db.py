import asyncio
import aiosqlite
import asyncpg
import datetime as dt
import json
import logging
import os
import pathlib
import types

logger = logging.getLogger(__name__)

class PostgresBotDB:
    def __init__(self, bot):
        self.bot = bot
        self.logger = logger
        #connection pool, created in start()
        self.pool = None

        #used in tracking which videos are skipped
        #important to note there may be data race issues
        #also skipped videos might be available in the cytube native logs
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

    async def start(self, user, password, database, host):
        self.logger.info('Connecting to database ' + database + '@' + host)
        self.pool = await asyncpg.create_pool(user=user, password=password, database=database, host=host)
        self.logger.info('Connected to database')
        await self.create_tables()
        return self

    async def create_tables(self):
        async with self.pool.acquire() as connection:
            self.logger.debug('Creating tables')
            async with connection.transaction():
                sql_setup_dir = pathlib.Path('sql/setup').resolve()
                self.logger.info(f'Looking for setup queries in {sql_setup_dir}')
                #Run all queries in sql/setup/tables, then run all queries in sql/setup/views
                for rr_fp in (pathlib.Path('sql/setup/tables'), pathlib.Path('sql/setup/views')):
                    for root, dirs, files in os.walk(rr_fp):
                        for fp in files:
                            fp = pathlib.Path(root) / pathlib.Path(fp)
                            if fp.suffix != '.sql': continue
                            with open(fp) as f: query = f.read()
                            self.logger.debug(f'Running query {fp}')
                            await connection.execute(query)

    async def log_event(self, timestamp, event, data):
        self.logger.debug('Logging event ' + str(event) + ': ' + str(data))
        data = json.dumps(data)
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                await connection.execute('INSERT INTO events VALUES($1, $2, $3)', timestamp, event, data)

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
