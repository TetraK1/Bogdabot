import discord
import asyncio
import json
import datetime as dt

with open('config.json') as f: CONFIG = json.loads(f.read())

class DiscordClient(discord.Client):
    def __init__(self, bot, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = bot

        self.last_deleted_uid = None

    async def start(self):
        await super().start(CONFIG['discord']['token'])

    async def on_ready(self):
        self.del_vids_channel = self.get_channel(CONFIG['discord']['deleted-vids-channel'])
        self.bot.on('delete', self.handle_vid_delete)
        self.bot.on('chatMsg', self.handle_chatMsg)
        #await self.del_vids_channel.send('ready')

    async def handle_vid_delete(self, data):
        self.last_deleted_uid = data['uid']

    async def handle_chatMsg(self, data):
        #on bot event 'chatMsg'
        if data['msg'].split(' ', 1)[0] != 'deleted': return
        try:
            if data['meta']['action'] != True or data['meta']['addClass'] != 'action': return
        except KeyError: return
        embed = discord.Embed()
        embed.title = data['msg'].split('"', 1)[1].rsplit('"', 1)[0]
        embed.type = 'rich'
        embed.set_author(name='Video deleted')
        embed.color = 0xFF6666
        embed.add_field(name='Deleted by', value=data['username'])
        await self.del_vids_channel.send(embed=embed)