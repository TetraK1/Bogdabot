import socketio
import asyncio

from db import BotDB
from userlist import Userlist, User
from chatcommands import RollCommand

class Event:
    def __init__(self):
        self.handlers = []

    def trigger(self, data):
        for f in self.handlers:
            asyncio.create_task(f(data))

    def register(self, handler):
        if handler not in self.handlers: self.handlers.append(handler)
    
    def remove(self, handler): self.handlers.remove(handler)

    def remove_all(self): self.handlers = []

class Bot:
    def __init__(self, **kwargs):
        self.socket = socketio.AsyncClient(**kwargs)
        self.db = BotDB()
        self.events = {}
        self.userlist = Userlist()

    def setup_handlers(self):
        printable_events = [
            'chatMsg',
            'usercount',
            #'userlist',
        ]
        for e in printable_events:
            def fuck_closures(e):
                async def print_event(data): print(e + ':', data)
                return print_event
            self.on(e, fuck_closures(e))

        self.on('chatMsg', self.db.log_chat_message)
        self.on('usercount', self.db.log_usercount)
        self.on('userlist', self.userlist.load_from_userlist)
        self.on('userLeave', self.userlist.on_user_leave)
        self.on('chatMsg', RollCommand(self).on_chat_message)

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
        await self.socket.emit('joinChannel', {'name':channel})
        #await asyncio.sleep(1)
        self.setup_handlers()

    async def login(self, username, password):
        await self.socket.emit('login', {'name':username, 'pw':password})

    async def send_chat_message(self, msg):
        data = {'msg': msg, 'meta': {}}
        await self.socket.emit('chatMsg', data)

    async def send_pm(self, to, msg):
        data = {'to': to, 'msg':msg, 'meta':{'modflair':1}}
        await self.socket.emit('pm', data)