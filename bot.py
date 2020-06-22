import asyncio
import datetime as dt
import logging
import json

import botsocket
from userlist import Userlist, User
from chatcommands import ChatCommands
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
        self.socket = botsocket.AsyncClient()
        self.events = {}
        self.userlist = Userlist(self)
        self.playlist = Playlist(self)
        self.db = None
        self.discord = None
        self.chat_commands = ChatCommands(self)
        #start_time stores when the bot connected to the room, so we can know
        #which chat messages are old and shouldn't be processed
        self.start_time = None

    async def start(self):
        self.logger.info('Starting bot')
        await self.connect(self.server)
        await self.login(self.username, self.password)
        await self.join_channel(self.channel)
        await self.send_chat_message('Now handling commands')
        self.start_time = dt.datetime.now()
        self.logger.info('Bot started')

    async def connect(self, server):
        self.logger.info('Connecting to ' + server)
        await self.socket.connect(server)
        self.logger.info('Connected to ' + server)

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
        botdb = db.PostgresBotDB(self)
        await botdb.start(username, password, database, host)
        self.db = botdb

    async def add_discord(self, token):
        dc = DiscordClient(self)
        await dc.start(token)
        self.discord = dc