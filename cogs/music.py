import discord
from discord.ext import commands

import requests
from bs4 import BeautifulSoup

import os
import codecs
import time
import json
import re

import logging
import asyncio
from async_timeout import timeout

import youtube_dl


_YOUTUBE_ = "youtube"

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

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

    @classmethod
    async def regather_stream(cls, data, *, loop):
        """Used for preparing a stream, instead of downloading.
        Since Youtube Streaming links expire."""

        loop = loop or asyncio.get_event_loop()
        requester = data['requester']

        to_run = partial(ytdl.extract_info, url=data['webpage_url'], download=False)
        data = await loop.run_in_executor(None, to_run)

        return cls(discord.FFmpegPCMAudio(data['url']), data=data, requester=requester)


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
            # mark the event as not set
            self.next.clear()

            try:
                # Wait for the next song. If we timeout cancel the player and disconnect...
                async with timeout(300):    # 5 minutes...
                    source = await self.queue.get()
            except asyncio.TimeoutError:
                return self.destroy(self.ctx.guild)

            if not isinstance(source, YTDLSource):
                # Source was probably a stream (not downloaded)
                # So we should regather to prevent stream expiration
                try:
                    source = await YTDLSource.regather_stream(source, loop=self.bot.loop)
                except Exception as e:
                    await ctx.send(f'There was an error processing your song.\n'
                                             f'```css\n[{e}]\n```')
                    continue

            async with self.ctx.typing():
                self.ctx.voice_client.play(source, after=lambda _: self.bot.loop.call_soon_threadsafe(self.next.set))   # set the event avalible after the song
            await self.ctx.send('Now playing: {}'.format(source.title))

            # wait for the event to be set
            await self.next.wait()

            # Make sure the FFmpeg process is cleaned up.
            source.cleanup()

    def destroy(self, guild):
         """Disconnect and cleanup the player."""
         return self.bot.loop.create_task(self.ctx.cog.cleanup(guild))


class Music(commands.Cog):
    def __init__(self, bot):
        setupLogPath()
        printLog("[I][Music.__init__] %s.py " % (os.path.basename(__file__).split('.')[0]))

        self.bot = bot
        self.url_source = None # set in check_source
        self.players = {}

    async def cleanup(self, guild):
        try:
            await guild.voice_client.disconnect()
        except AttributeError:
            pass

        try:
            del self.players[guild.id]
        except KeyError:
            pass

    # !!! need to be review !!!
    async def ensure_voice(self, ctx):
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            await ctx.send("You are not connected to a voice channel.")
            raise commands.CommandError("Author not connected to a voice channel.")

    def get_player(self, ctx):
        """Retrieve the guild player, or generate one."""
        try:
            player = self.players[ctx.guild.id]
        except KeyError:
            player = MusicPlayer(self.bot, ctx)
            self.players[ctx.guild.id] = player
        return player

    def check_source(self, url):
        """check the url source"""
        ytl = r'https://www.youtube.com.*'
        try:
            if re.fullmatch(ytl, url):
                self.url_source = _YOUTUBE_
                return _YOUTUBE_
        except Exception as e:
            printLog("[check_source][E] Unexcepted Error : %s" % e)


    def parse_youtube_url(self, url):
        match = re.search("list=\w+", url)
        if not match:
            return url
        else:
            return url.split(match)[0] + match

    def is_playlist(self, url):
        if self.url_source == _YOUTUBE_:
            match = re.search("list=\w+", url)
            return False if not match else True

    async def get_playlist(self, url):
        try:
            # oriinal url be like:
            # https://www.youtube.com/watch?v=ouLndhBRL4w&list=PL1urwPG3M3NKahUbWDj_Y1qgwtRvhMpN7&index=6
            url = "https://www.youtube.com/playlist?" + url.split("&")[1]
            print(url)
            # 發送 GET 請求取得網頁內容
            response = requests.get(url)
            html = response.text
            with open("html.txt", "w", encoding="utf-8") as f:
                f.write(html)
            # 使用 BeautifulSoup 解析 HTML
            soup = BeautifulSoup(html, 'html.parser')

            # 找出所有影片連結所在的元素 by css selector
            video_links = soup.select('a.yt-simple-endpoint.style-scope.ytd-playlist-video-renderer')
            print("sdfsdf")
            print(video_links)
            # 印出每個影片的 URL
            for link in video_links:
                video_url = 'https://www.youtube.com' + link['href']
                print(video_url)
            print("sdfsdfsdf")
        except Exception as e:
            printLog("[get_playlist][E] Unexcepted Error : %s" % e)


    @commands.command()
    async def join(self, ctx, *, channel: discord.VoiceChannel):
        """Joins a voice channel"""

        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)

        await channel.connect()

    @commands.command(name="play", help="Play music as stream")
    async def play(self, ctx, *, url):
        """Streams from a url (same as yt, but doesn't predownload)"""

        if not ctx.voice_client:
            await self.ensure_voice(ctx)

        # self.check_source(url)
        # if self.url_source == _YOUTUBE_:
        #     if self.is_playlist(url):
        #         list = await self.get_playlist(url)  # to be opt


        player = self.get_player(ctx)

        # If download is False, source will be a dict which will be used later to regather the stream.
        # If download is True, source will be a discord.FFmpegPCMAudio with a VolumeTransformer.
        source = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)

        await player.queue.put(source)


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



def setupLogPath():
    global g_logFileName

    parentDir = os.path.join(os.getcwd(), os.pardir)
    logDir = parentDir + "/log"
    if not os.path.exists(logDir):
        os.makedirs(logDir)
    g_logFileName = os.path.join(logDir, (os.path.basename(__file__)[:-3] + ".log"))

def getDateTimeFormat():
    strDateTime = "[%s]" % (time.strftime("%Y/%m/%d %H:%M:%S", time.localtime()))
    return strDateTime

def printLog(strPrintLine):
    fileLog = codecs.open(g_logFileName, 'a', "utf-8")
    print(strPrintLine)
    fileLog.write("%s%s\r\n" % (getDateTimeFormat(), strPrintLine))
    fileLog.close()


# bot = commands.Bot(command_prefix=commands.when_mentioned_or("!"),
#                    description='Relatively simple music bot example')
def setup(bot):
    bot.add_cog(Music(bot))
