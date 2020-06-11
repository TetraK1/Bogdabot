import socketio
import asyncio
import json
import logging
from logging import DEBUG, INFO, WARN

from bot import Bot
from db import PostgresBotDB
import userlist

logging.basicConfig(level=logging.INFO)
logging.getLogger('engineio').setLevel(WARN)
logging.getLogger('socketio').setLevel(WARN)
#logging.getLogger('bot').setLevel(WARN)
logging.getLogger('db').setLevel(INFO)
#logging.getLogger('userlist').setLevel(WARN)
#logging.getLogger('playlist').setLevel(WARN)
#logging.getLogger('discord').setLevel(DEBUG)

with open('config.json') as f: CONFIG = json.loads(f.read())

async def main():
    bot = Bot(CONFIG['server'], CONFIG['channel'], CONFIG['username'], CONFIG['password'])

    db_config = CONFIG['database']
    await bot.add_db(db_config['username'], db_config['password'], db_config['database'], db_config['host'])

    
    discord_config = CONFIG['discord']
    print('llllllllllllllllllllllllllllll')
    await bot.add_discord(discord_config['token'])
    print('#######################################')
    bot.discord.del_vids_channel = discord_config['deleted-vids-channel']
    
    await bot.start()
    await bot.socket.wait()

if __name__ == '__main__':
    asyncio.run(main())