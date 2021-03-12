import asyncio
import logging
import prompt_toolkit

def stop(bot, text):
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for t in tasks: t.cancel()
    raise EOFError

def getplaylist(bot, text):
    output = 'Playlist:\n'
    for i, v in enumerate(bot.playlist.videos):
        output += f'\t{i+1}: ({v.uid}) \033[92m{v.title}\033[0m via {v.queueby} ({v.id})\n'
    print(output)

def say(bot, text):
    text = text.split(' ', 1)
    if len(text) < 2: return
    command, text = text
    asyncio.create_task(bot.send_chat_message(text))

def command_help(bot, text):
    command_names = sorted(commands.keys())
    output = 'Available commands:' + '\n\t' + '\n\t'.join(sommand_names)
    print(output)

commands = {
    'exit': stop,
    'getplaylist': getplaylist,
    'say': say,
    'help': command_help,
}

async def interactive_shell(bot, loop):

    logger = logging.getLogger('cmd')
    session = prompt_toolkit.shortcuts.PromptSession('cmd: ')

    while True:
        try:
            result = await session.prompt_async(set_exception_handler=False)

            command = result.split(' ')[0]
            logger.info(f'Running command "{result}"')
            if command in commands: 
                commands[command](bot, result)
            else:
                logger.info(f'Command "{command}" not recognised')

        except (EOFError, KeyboardInterrupt):
            loop.stop()
            break