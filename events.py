import asyncio

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

