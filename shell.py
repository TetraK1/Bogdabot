import asyncio
import logging
import prompt_toolkit

def stop(bot, text):
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for t in tasks: t.cancel()
    raise EOFError

def getplaylist(bot, text):
    print('Playlist:')
    for i, v in enumerate(bot.playlist.videos):
        print('\t' + str(i) + ':', v.title, '(' + v.id + ')')

def say(bot, text):
    if result.split(' ')[0] == 'say':
        loop.create_task(bot.send_chat_message(' '.join(result.split(' ')[1:])))

commands = {
    'exit': stop,
    'getplaylist': getplaylist,
    'say': say,
}

async def interactive_shell(bot, loop):

    logger = logging.getLogger('cmd')
    session = prompt_toolkit.shortcuts.PromptSession('cmd: ')

    while True:
        try:
            result = await session.prompt_async(set_exception_handler=False)
            command = result.split(' ')[0]
            logger.info(f'Running command "{result}"')
            if result in commands: commands[command](bot, result)

        except (EOFError, KeyboardInterrupt):
            loop.stop()
            break