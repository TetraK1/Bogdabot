import socketio
import asyncio
import json
import logging

from bot import Bot
from db import PostgresBotDB
import userlist

logging.basicConfig(level=logging.DEBUG)
with open('config.json') as f: config = json.loads(f.read())

db_config = config['database']



async def main():
    bot = Bot(config['server'], config['channel'], config['username'], config['password'])
    bot.db = PostgresBotDB(bot)
    bot.logger.setLevel(logging.DEBUG)
    bot.db.logger.setLevel(logging.DEBUG)
    userlist.logger.setLevel(logging.DEBUG)
    await bot.db.connect(db_config['username'], db_config['password'], db_config['database'], db_config['host'])
    await bot.start()
    await bot.socket.wait()

asyncio.run(main())