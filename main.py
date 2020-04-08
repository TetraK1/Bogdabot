import socketio
import asyncio
import json
from bot import Bot

with open('config.json') as f: config = json.loads(f.read())

async def main():
    bot = Bot(logger=True)
    await bot.connect(config['server'])
    await bot.login(config['username'], config['password'])
    await bot.join_channel(config['channel'])
    await bot.socket.wait()

asyncio.run(main())