import asyncio
import logging
import prompt_toolkit

async def interactive_shell(bot, loop):

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