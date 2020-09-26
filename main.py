import asyncio
import json
import logging
import logging.config
import urllib.parse
import urllib.request
import yaml

from bot import Bot
from db import PostgresBotDB
import userlist

import prompt_toolkit.patch_stdout
import prompt_toolkit.shortcuts

loop = asyncio.get_event_loop()
logger = logging.getLogger()

bot = None

async def interactive_shell():

    def stop():
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        for t in tasks: t.cancel()
        loop.stop()

    logger = logging.getLogger('cmd')
    session = prompt_toolkit.shortcuts.PromptSession('cmd: ')

    while True:
        try:
            result = await session.prompt_async(set_exception_handler=False)
            logger.info(f'Running command "{result}"')
            if result == 'exit':
                stop()
                break

            if result == 'getplaylist':
                print('Playlist:')
                for i, v in enumerate(bot.playlist.videos):
                    print('\t' + str(i) + ':', v.title, '(' + v.id + ')')

        except (EOFError, KeyboardInterrupt):
            stop()
            break

def get_room_server(main_server, room):
    '''main_server should include scheme e.g. "http://cytu.be"
    
    is blocking
    '''
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
    global bot
    bot = Bot(room_server, CONFIG['channel'], CONFIG['username'], CONFIG['password'])

    db_config = CONFIG['database']
    await bot.add_db(db_config['username'], db_config['password'], db_config['database'], db_config['host'])
    
    discord_config = CONFIG['discord']
    await bot.add_discord(discord_config['token'])
    await bot.discord.add_del_vids_channel(discord_config['deleted-vids-channel'])
    
    await bot.start()
    asyncio.create_task(bot.socket.wait())

if __name__ == '__main__':
    with prompt_toolkit.patch_stdout.patch_stdout():

        with open('logconfig.yml') as f: lc = yaml.safe_load(f.read())
        logging.config.dictConfig(lc)
        try:
            with open('config.yml') as f: CONFIG = yaml.safe_load(f.read())
        except FileNotFoundError:
            with open('config.json') as f: CONFIG = yaml.safe_load(f.read())
        logger.warn('Config.json should be moved to config.yml')

        loop.create_task(interactive_shell())
        loop.create_task(main())
        loop.run_forever()
