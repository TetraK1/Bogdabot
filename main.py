import socketio
import asyncio
import json
import logging
import urllib.parse
import urllib.request

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

#logging.getLogger('botsocket').setLevel(logging.DEBUG)
logging.getLogger('engineio').setLevel(logging.WARN)
logging.getLogger('socketio').setLevel(logging.WARN)
#logging.getLogger('discordbot').setLevel(logging.DEBUG)
#logging.getLogger('discord').setLevel(logging.WARN)
#logging.getLogger('bot').setLevel(WARN)
#logging.getLogger('db').setLevel(INFO)
#logging.getLogger('userlist').setLevel(WARN)
#logging.getLogger('playlist').setLevel(WARN)


with open('config.json') as f: CONFIG = json.loads(f.read())

def get_room_server(main_server, room):
    '''main_server should include scheme e.g. "http://cytu.be"'''
    url = urllib.parse.urlparse(main_server)
    url = urllib.parse.ParseResult(url.scheme, url.netloc, f'/socketconfig/{room}.json', url.params, url.query, url.fragment)
    url = urllib.parse.urlunparse(url)
    with urllib.request.urlopen(url) as response:
        r = json.loads(response.read())
    return r['servers'][0]['url']

async def main():
    logger.info(f'Retrieving channel server from {CONFIG["server"]}')
    room_server = await loop.run_in_executor(None, get_room_server, CONFIG['server'], CONFIG['channel'])
    logger.info(f'Room {CONFIG["channel"]} on server {room_server}')

    bot = Bot(room_server, CONFIG['channel'], CONFIG['username'], CONFIG['password'])

    db_config = CONFIG['database']
    await bot.add_db(db_config['username'], db_config['password'], db_config['database'], db_config['host'])
    
    discord_config = CONFIG['discord']
    await bot.add_discord(discord_config['token'])
    await bot.discord.add_del_vids_channel(discord_config['deleted-vids-channel'])
    
    await bot.start()
    await bot.socket.wait()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())