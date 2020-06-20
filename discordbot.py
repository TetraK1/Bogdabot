import discord
import asyncio
import json
import datetime as dt
import logging

with open('config.json') as f: CONFIG = json.loads(f.read())

logger = logging.getLogger(__name__)

class DiscordClient(discord.Client):
    def __init__(self, bot, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = bot
        self.last_deleted_uid = None
        self.del_vids_channel = None
        self.logger = logger

    async def start(self, token):
        self.logger.info('Starting discord')
        self.bot.on('delete', self.handle_vid_delete)
        self.bot.on('chatMsg', self.handle_chatMsg)
        asyncio.create_task(super().start(token))

    async def handle_vid_delete(self, data):
        self.last_deleted_uid = data['uid']

    async def handle_chatMsg(self, data):
        #on bot event 'chatMsg'
        if self.bot.db is None: return
        if not self.del_vids_channel: return
        if data['msg'].split(' ', 1)[0] != 'deleted': return
        try:
            if data['meta']['action'] != True or data['meta']['addClass'] != 'action': return
        except KeyError: return
        if not self.bot.userlist[data['username']].rank >= 2: return

        title = data['msg'].split('"', 1)[1].rsplit('"', 1)[0]
        async with self.bot.db.pool.acquire() as connection:
            async with connection.transaction():
                db_result = await connection.fetch("""select videos.video_type, videos.video_id, videos.title, video_adds.from_username
                    from videos
                    inner join video_adds
                    on videos.video_id = video_adds.video_id and videos.video_type = video_adds.video_type
                    where videos.title = $1
                    order by video_adds.timestamp desc 
                    limit 1
                    """, 
                    title
                )
        from_username = db_result[0]['from_username']
        embed = discord.Embed()
        embed.title = title
        embed.type = 'rich'
        embed.set_author(name='Video deleted')
        embed.color = 0xFF6666
        embed.add_field(name='Posted by', value=from_username)
        embed.add_field(name='Deleted by', value=data['username'])

        if x['type'] == 'yt':
            embed.description = 'https://youtu.be/' + x['id']

        await self.del_vids_channel.send(embed=embed)