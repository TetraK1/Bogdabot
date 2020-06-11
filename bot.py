import asyncio
import datetime as dt
import logging
import json
import socketio

from userlist import Userlist, User
from chatcommands import ChatCommands
from events import Event
from playlist import Playlist
from discordbot import DiscordClient
import db

class Bot:
    def __init__(self, server, channel, username, password):
        self.server = server
        self.channel = channel
        self.username = username
        self.password = password

        self.logger = logging.getLogger(__name__)
        #socket should probably be split out into a subclass to make the
        #trigger patching in db easier and whatever else
        self.socket = socketio.AsyncClient()
        self.events = {}
        self.userlist = Userlist(self)
        self.playlist = Playlist(self)
        self.db = None
        self.discord = None
        #Used to check whether the bot has logged in and processed old chat messages
        self.chat_commands = ChatCommands(self)
        #start_time stores when the bot connected to the room, so we can know
        #which chat messages are old and shouldn't be processed
        self.start_time = None

    async def start(self):
        self.logger.info('Starting bot')
        self.start_time = dt.datetime.now()
        await self.connect(self.server)
        await self.login(self.username, self.password)
        await self.join_channel(self.channel)
        await self.send_chat_message('Now handling commands')

    async def connect(self, server):
        self.logger.info('Connecting to ' + server)
        await self.socket.connect(server)

    async def join_channel(self, channel):
        self.logger.info('Joining channel ' + channel)
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

    async def add_db(self, username, password, database, host):
        self.db = db.PostgresBotDB(self)
        await self.db.start(username, password, database, host)

    async def add_discord(self, token):
        self.discord = DiscordClient(self)
        await self.discord.start(token)

    async def setup_post_handlers(self):
        self.on('chatMsg', self.chat_commands.on_chat_message)

    def on(self, event, handler):
        #handler needs to be async
        if event not in self.events:
            self.events[event] = Event()
            self.socket.on(event, self.events[event].trigger)
        self.events[event].register(handler)

    def off(self, event, handler=None):
        if handler is None: self.events[event].remove_all()
        else: self.events[event].remove(handler)