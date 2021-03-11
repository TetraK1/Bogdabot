import asyncio
import logging
import prompt_toolkit

def stop(bot):
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for t in tasks: t.cancel()
    raise EOFError

def getplaylist(bot):
    print('Playlist:')
    for i, v in enumerate(bot.playlist.videos):
        print('\t' + str(i) + ':', v.title, '(' + v.id + ')')

commands = {
    'exit': stop,
    'getplaylist': getplaylist,
}

async def interactive_shell(bot, loop):

    logger = logging.getLogger('cmd')
    session = prompt_toolkit.shortcuts.PromptSession('cmd: ')

    while True:
        try:
            result = await session.prompt_async(set_exception_handler=False)
            logger.info(f'Running command "{result}"')
            if result in commands: commands[result](bot)

        except (EOFError, KeyboardInterrupt):
            loop.stop()
            break