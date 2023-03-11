import discord
from discord.ext import commands

import os
import asyncio
from async_timeout import timeout

import youtube_dl




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

class MusicPlayer:
    def __init__(self, bot, ctx):
        self.bot = bot
        self.ctx = ctx
        self.queue = asyncio.Queue()
        self.next = asyncio.Event()

        bot.loop.create_task(self.player_loop())

    async def player_loop(self):
        """ main player loop """

        # Waits until the client’s internal cache is all ready.
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            self.next.clear()

            try:
                # Wait for the next song. If we timeout cancel the player and disconnect...
                async with timeout(300):    # 5 minutes...
                    source = await self.queue.get()
            except asyncio.TimeoutError:
                await self.ctx.voice_client.disconnect()

            if not isinstance(source, YTDLSource):
                # Source was probably a stream (not downloaded)
                # So we should regather to prevent stream expiration
                try:
                    source = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
                except Exception as e:
                    await ctx.send(f'There was an error processing your song.\n'
                                             f'```css\n[{e}]\n```')
                    continue

            self.ctx.voice_client.play(source, after=lambda _: self.bot.loop.call_soon_threadsafe(self.next.set))
            await self.ctx.send('Now playing: {}'.format(source.title))

            await self.next.wait()

            # Make sure the FFmpeg process is cleaned up.
            source.cleanup()

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

    @commands.command(name="play", help="Play music as stream")
    async def play(self, ctx, *, url):
        """Streams from a url (same as yt, but doesn't predownload)"""

        player = MusicPlayer(self.bot, ctx)

        # If download is False, source will be a dict which will be used later to regather the stream.
        # If download is True, source will be a discord.FFmpegPCMAudio with a VolumeTransformer.
        source = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)

        await player.queue.put(source)

        # async with ctx.typing():
        #     player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
        #     ctx.voice_client.play(player, after=lambda e: print('Player error: %s' % e) if e else None)
        # await ctx.send('Now playing: {}'.format(player.title))

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

    @play.before_invoke
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
