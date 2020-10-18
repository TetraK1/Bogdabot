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

async def main():
    logger.info(f'Retrieving channel server from {CONFIG["server"]}')
    room_server = await loop.run_in_executor(None, utils.get_room_server, CONFIG['server'], CONFIG['channel'])
    logger.info(f'Room {CONFIG["channel"]} on server {room_server}')
    global bot
    bot = Bot(room_server, CONFIG['channel'], CONFIG['username'], CONFIG['password'])

    await db.init(bot, CONFIG)
    await discordbot.init(bot, CONFIG)
    
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

        loop.create_task(shell.interactive_shell(bot, loop))
        loop.create_task(main())
        loop.run_forever()
