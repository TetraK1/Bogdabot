import socketio
import asyncio
import json

from db import SqliteBotDB
from userlist import Userlist, User
from chatcommands import RollCommand, QuoteCommand
from events import Event

class Bot:
    def __init__(self, database=None, **kwargs):
        self.socket = socketio.AsyncClient(**kwargs)
        self.db = database
        if database is None: self.db = SqliteBotDB('bot.db')
        self.events = {}
        self.userlist = Userlist()

    async def setup_pre_handlers(self):
        await self.db.connect()
        printable_events = [
            #'chatMsg',
            #'usercount',
            #'userlist',
            #'kick',
            #'playlist',
            #'setPlaylistMeta',
        ]
        for e in printable_events:
            def fuck_closures(e):
                async def print_event(data): print(e + ':', data)
                return print_event
            self.on(e, fuck_closures(e))
        
        self.on('usercount', self.db.log_usercount)
        self.on('userlist', self.userlist.load_from_userlist)
        self.on('userLeave', self.userlist.on_user_leave)
        self.on('addUser', self.userlist.on_add_user)

        async def yuh(data):
            with open('playlist.json', 'w') as f:
                json.dump(data, f)

        self.on('playlist', yuh)

    async def setup_chat_handlers(self):
        self.on('chatMsg', self.db.log_chat_message)
        self.on('chatMsg', RollCommand(self))
        self.on('chatMsg', QuoteCommand(self))

    def on(self, event, handler):
        #handler needs to be async
        if event not in self.events:
            self.events[event] = Event()
            self.socket.on(event, self.events[event].trigger)
        self.events[event].register(handler)

    def off(self, event, handler=None):
        if handler is None: self.events[event].remove_all()
        else: self.events[event].remove(handler)

    async def connect(self, server):
        await self.socket.connect(server)

    async def join_channel(self, channel):
        await self.setup_pre_handlers()
        await self.socket.emit('joinChannel', {'name':channel})
        await asyncio.sleep(1)
        await self.setup_chat_handlers()
        #await self.send_chat_message('Now handling commands')

    async def login(self, username, password):
        await self.socket.emit('login', {'name':username, 'pw':password})

    async def send_chat_message(self, msg):
        data = {'msg': msg, 'meta': {}}
        await self.socket.emit('chatMsg', data)

    async def send_pm(self, to, msg):
        data = {'to': to, 'msg':msg, 'meta':{'modflair':1}}
        await self.socket.emit('pm', data)