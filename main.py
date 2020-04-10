import socketio
import asyncio
import json
from bot import Bot
from db import SqliteBotDB, PostgresBotDB

with open('config.json') as f: config = json.loads(f.read())

db = config['database']
db = PostgresBotDB(db['username'], db['password'], db['database'], db['host'])

bot = Bot(database=db, logger=True)

async def main():
    await bot.connect(config['server'])
    await bot.login(config['username'], config['password'])
    await bot.join_channel(config['channel'])
    await bot.socket.wait()

asyncio.run(main())