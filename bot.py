import socketio
import asyncio
import json
import logging

from userlist import Userlist, User
from chatcommands import ChatCommands
from events import Event
from playlist import Playlist
from discordbot import DiscordClient

class Bot:
    def __init__(self, server, channel, username, password):
        self.server = server
        self.channel = channel
        self.username = username
        self.password = password

        self.logger = logging.getLogger(__name__)
        self.socket = socketio.AsyncClient()
        self.events = {}
        self.userlist = Userlist(self)
        self.playlist = Playlist(self)
        self.db = None
        self.discord_bot = DiscordClient(self)
        #Used to check whether the bot has logged in and processed old chat messages
        self.chat_commands = ChatCommands(self)
        self.started = asyncio.Event()

    async def start(self):
        self.logger.info('Starting bot')
        await self.connect(self.server)
        await self.login(self.username, self.password)
        await self.join_channel(self.channel)
        await self.setup_pre_handlers()
        await asyncio.sleep(1)
        await self.setup_post_handlers()
        #await self.send_chat_message('Now handling commands')

    async def connect(self, server):
        self.logger.info('Connecting to ' + server)
        await self.socket.connect(server)

    async def join_channel(self, channel):
        self.logger.info('Joining channel ' + channel)
        await self.setup_pre_handlers()
        await self.socket.emit('joinChannel', {'name':channel})

    async def login(self, username, password):
        self.logger.info('Joining as ' + username)
        await self.socket.emit('login', {'name':username, 'pw':password})

    async def send_chat_message(self, msg):
        data = {'msg': msg, 'meta': {}}
        await self.socket.emit('chatMsg', data)

    async def send_pm(self, to, msg):
        data = {'to': to, 'msg':msg, 'meta':{}}
        await self.socket.emit('pm', data)

    async def setup_pre_handlers(self):
        printable_events = [
            #'chatMsg',
            #'usercount',
            #'userlist',
            #'kick',
            #'playlist',
            #'login',
            #'setPlaylistMeta',
            #'queue',
            'changeMedia'
        ]
        for e in printable_events:
            def fuck_closures(e):
                async def print_event(data): self.logger.debug(e + ' event: ' + str(data))
                return print_event
            self.on(e, fuck_closures(e))

    async def setup_post_handlers(self):
        self.on('chatMsg', self.chat_commands.on_chat_message)
        async def fuck_rin(data):
            if data['username'] != 'rinpleasesoldmen': return
            self.send_pm('rinpleasesoldmen', 'shut the fuck up rin')
        self.on('chatMsg', fuck_rin)
        await self.discord_bot.start()

    def on(self, event, handler):
        #handler needs to be async
        if event not in self.events:
            self.events[event] = Event()
            self.socket.on(event, self.events[event].trigger)
        self.events[event].register(handler)

    def off(self, event, handler=None):
        if handler is None: self.events[event].remove_all()
        else: self.events[event].remove(handler)