import socketio
import asyncio
import json
import logging

from bot import Bot
from db import PostgresBotDB
import userlist

#logging setup should get moved to an INI file of the format used by the
#logging library
ch = logging.StreamHandler()

fh = logging.FileHandler('log.txt', mode='w')

formatter = logging.Formatter(
    fmt='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
    datefmt='%y.%m.%d %H:%M:%S'
)
ch.setFormatter(formatter), fh.setFormatter(formatter)

logger = logging.getLogger()
logger.addHandler(ch)
logger.addHandler(fh)
logger.setLevel(logging.INFO)

logging.getLogger('engineio').setLevel(logging.WARN)
logging.getLogger('socketio').setLevel(logging.WARN)
#logging.getLogger('discordbot').setLevel(logging.DEBUG)
logging.getLogger('discord').setLevel(logging.WARN)
#logging.getLogger('bot').setLevel(WARN)
#logging.getLogger('db').setLevel(INFO)
#logging.getLogger('userlist').setLevel(WARN)
#logging.getLogger('playlist').setLevel(WARN)


with open('config.json') as f: CONFIG = json.loads(f.read())

async def main():
    bot = Bot(CONFIG['server'], CONFIG['channel'], CONFIG['username'], CONFIG['password'])

    db_config = CONFIG['database']
    await bot.add_db(db_config['username'], db_config['password'], db_config['database'], db_config['host'])
    
    discord_config = CONFIG['discord']
    await bot.add_discord(discord_config['token'])
    print(type(discord_config['deleted-vids-channel']))
    await bot.discord.add_del_vids_channel(discord_config['deleted-vids-channel'])
    
    await bot.start()
    await bot.socket.wait()

if __name__ == '__main__':
    asyncio.run(main())