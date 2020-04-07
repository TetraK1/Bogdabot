import asyncio
import aiosqlite

class BotDB:
    def __init__(self):
        asyncio.create_task(self.create_tables())

    async def create_tables(self):
        self.db = await aiosqlite.connect('bot.db')
        await self.db.execute('CREATE TABLE IF NOT EXISTS chat(timestamp INTEGER, username TEXT, msg TEXT)')
        await self.db.execute('CREATE TABLE IF NOT EXISTS users(uname TEXT)')
        #type is where it's from e.g. 'yt'
        await self.db.execute('CREATE TABLE IF NOT EXISTS videos(type TEXT, id TEXT, duration_ms INTEGER, title TEXT, PRIMARY KEY (type, id))')
        await self.db.execute('CREATE TABLE IF NOT EXISTS user_count(timestamp INTEGER, count INTEGER)')
        await self.db.commit()

    async def log_chat_message(self, data):
        data = (data['time'], data['username'], data['msg'])
        await self.db.execute('INSERT INTO chat VALUES(?, ?, ?)', data)
        await self.db.commit()

    async def log_usercount(self, data):
        data = data,
        await self.db.execute('INSERT INTO user_count VALUES(CURRENT_TIMESTAMP, ?)', data)
        await self.db.commit()

    async def log_video(self, data):
        pass
    
    async def get_quote(self, username):
        x = await self.db.execute("SELECT username, msg, timestamp FROM chat WHERE username = ? COLLATE NOCASE ORDER BY RANDOM() LIMIT 1", (username,))
        return await x.fetchall()