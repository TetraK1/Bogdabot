import asyncio
import socketio
import logging

logger = logging.getLogger(__name__)

class AsyncClient:
    '''Main purpose of this class was to add many handlers to one event, and
    to allow for a wildcard event to be subscribed to, which registers a
    a handler to receive all events.
    '''
    def __init__(self, *args, **kwargs):
        self.logger = logger
        self.siosock = socketio.AsyncClient()

        self.ns = socketio.AsyncClientNamespace('/')
        self.ns.trigger_event = self.trigger_event
        self.siosock.register_namespace(self.ns)

        #dict keyed by eventname, and dict values are lists of handlers
        #handlers can be funcs or coroutines
        self.handlers = {}

    def on(self, event, handler):
        '''Handler signature should be f(data) for most events, for wildcard
        event signature should be f(event, data)
        '''
        if event not in self.handlers: self.handlers[event] = []
        self.handlers[event].append(handler)

    def off(self, event, handler=None):
        '''If handler is not specified, all handlers for the event will be
        removed
        '''
        if handler is not None:
            self.handlers[event].remove(handler)
        else:
            self.handlers[event] = []

    def to_coroutine(self, f):
        '''Return f wrapped in a coroutine'''
        async def async_h(*args, **kwargs):
            return f(*args, **kwargs)
        return async_h

    def trigger_wildcard(self, event, data=None):
        if '*' not in self.handlers: return
        for f in self.handlers['*']:
            self.logger.debug(f'Firing wilcard handler {f.__name__} in response to {event}')
            asyncio.create_task(f(event, data))

    async def trigger_event(self, event, data=None):
        self.trigger_wildcard(event, data)
        if event not in self.handlers: return
        for f in self.handlers[event]:
            self.logger.debug(f'Firing handler {f.__name__} in response to {event}')
            asyncio.create_task(f(data))

    async def connect(self, *args, **kwargs): 
        return await self.siosock.connect(*args, **kwargs)

    async def emit(self, *args, **kwargs):
        return await self.siosock.emit(*args, **kwargs)

    async def wait(self, *args, **kwargs):
        return await self.siosock.wait(*args, **kwargs)