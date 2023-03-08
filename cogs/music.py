import os
import asyncio

import discord
import youtube_dl

from discord.ext import commands


# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''

# 設定音樂下載和轉換的參數
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}
ffmpeg_options = {
    'options': '-vn',
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"   # packet loss handler
}

# 建立音樂下載器
ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

# If you turn up Master volume, everything gets louder...headphones, CD, etc. PCM turns up the volume just for sound files,
# but CD volume would remain the same. Useful if you'd like MP3's to be louder than audio CD's.
class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    # The method takes in the URL as a parameter and returns the filename of the audio file which gets downloaded.
    @classmethod    # 一般函數的第一個參數指的是該物件的記憶體位置，classmethod的第一個參數指的是該類別的記憶體位置。用法類似static method
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # self.loop = False
        self.queue = []

    @commands.command()
    async def join(self, ctx, *, channel: discord.VoiceChannel):
        """Joins a voice channel"""

        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)

        await channel.connect()


    async def play(self, ctx):
        """Streams from a url (same as yt, but doesn't predownload)"""

        if not self.queue:
            return

        url = self.queue[0]

        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            #ctx.voice_client.play(player, after=lambda e: print('Player error: %s' % e) if e else None)
            ctx.voice_client.play(player, after=lambda e: self.queue.pop(0))
        await ctx.send('Now playing: {}'.format(player.title))

    @commands.command(name="play", help="Play music as stream")
    async def play_command(self, ctx, *, url):
        # 加入到播放队列中
        self.queue.append(url)

        #如果没有歌曲在播放，开始播放
        if len(self.queue) >= 1:
            await self.play(ctx)

    # @commands.command(help="Add a audio to playlist")
    # async def add(self, ctx, *, url):
    #     """add a audio to playlist"""
    #
    #     async with ctx.typing():
    #         player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
    #         self.queue.append(url)
    #
    #     await ctx.send('Added audio: {} to playlist'.format(player.title))

    # @commands.command(help="Start a playlist")
    # async def play_list(self, ctx):
    #     """start the playlist"""
    #
    #     async with ctx.typing():
    #         url = self.queue.pop(0)
    #
    #         if self.loop == True:
    #             self.queue.append(url)
    #
    #         player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
    #         ctx.voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop))
    #
    #     await ctx.send('Now playing: {}'.format(player.title))

    # @commands.command(name="queue", help="Check the playlist")
    # async def queue_(self, ctx):
    #     songs = []
    #     for url in self.queue:
    #         songs.append(url)
    #
    #     await ctx.send(songs)

    @commands.command()
    async def volume(self, ctx, volume: int):
        """Changes the player's volume"""

        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.")

        ctx.voice_client.source.volume = volume / 100
        await ctx.send("Changed volume to {}%".format(volume))

    @commands.command()
    async def pause(self, ctx):
        if ctx.voice_client.is_playing():
            await ctx.voice_client.pause()
        else:
            await ctx.send("I'm not playing anythin at this moment.")

    @commands.command()
    async def resume(self, ctx):
        if ctx.voice_client.is_paused():
            await ctx.voice_client.resume()
        else:
            await ctx.send("I was not playing anything before this.")

    @commands.command()
    async def stop(self, ctx):
        """Stops and disconnects the bot from voice"""

        await ctx.voice_client.disconnect()

    @play_command.before_invoke
    #@play_list.before_invoke
    #@yt.before_invoke
    #@stream.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()

# bot = commands.Bot(command_prefix=commands.when_mentioned_or("!"),
#                    description='Relatively simple music bot example')
def setup(bot):
    bot.add_cog(Music(bot))
