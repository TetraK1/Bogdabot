import asyncio
import json
import logging
import logging.config
import urllib.parse
import urllib.request
import yaml

from bot import Bot
import db
import discordbot
import userlist
import utils
import shell

import prompt_toolkit.patch_stdout
import prompt_toolkit.shortcuts

loop = asyncio.get_event_loop()
logger = logging.getLogger()

bot = None

async def start():
    logger.info(f'Retrieving channel server from {CONFIG["server"]}')
    room_server = await loop.run_in_executor(None, utils.get_room_server, CONFIG['server'], CONFIG['channel'])
    logger.info(f'Room {CONFIG["channel"]} on server {room_server}')
    global bot
    bot = Bot(room_server, CONFIG['channel'], CONFIG['username'], CONFIG['password'])

    if 'modules' in CONFIG:
        if 'database' in CONFIG['modules']:
            await db.init(bot, CONFIG)
        if 'discord' in CONFIG['modules']:
            await discordbot.init(bot, CONFIG)
    
    await bot.start()
    asyncio.create_task(shell.interactive_shell(bot, loop))
    while True:
        await bot.socket.wait()
        logger.error("Disconnected from server, reconnecting in 5 seconds")
        await asyncio.sleep(5)
        await bot.start()

if __name__ == '__main__':
    with prompt_toolkit.patch_stdout.patch_stdout():

        with open('logconfig.yml') as f: lc = yaml.safe_load(f.read())
        logging.config.dictConfig(lc)
        try:
            with open('config.yml') as f: CONFIG = yaml.safe_load(f.read())
        except FileNotFoundError:
            with open('config.json') as f: CONFIG = yaml.safe_load(f.read())
        logger.warn('Config.json should be moved to config.yml')

        loop.create_task(start())
        loop.run_forever()
