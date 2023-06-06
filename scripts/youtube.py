import discord
from discord.ext import commands

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
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
    def __init__(self, source, *, data, requester, volume=0.5):
        super().__init__(source, volume)
        self.requester = requester

        self.title = data.get('title')
        self.web_url = data.get('webpage_url')

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    def __getitem__(self, item: str):
        """Allows us to access attributes similar to a dict.
        This is only useful when NOT downloading.
        """
        return self.__getattribute__(item)

    # The method takes in the URL as a parameter and returns the filename of the audio file which gets downloaded.
    @classmethodthod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data, requester=ctx.author)

     @classmethod
     async def create_source(cls, ctx, search: str, *, loop, download=False):
        loop = loop or asyncio.get_event_loop()

        to_run = partial(ytdl.extract_info, url=search, download=download)
        data = await loop.run_in_executor(None, to_run)

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        await ctx.send(f'```ini\n[Added {data["title"]} to the Queue.]\n```', delete_after=15)

        if download:
            source = ytdl.prepare_filename(data)
        else:
            return {'webpage_url': data['webpage_url'], 'requester': ctx.author, 'title': data['title']}

        return cls(discord.FFmpegPCMAudio(source), data=data, requester=ctx.author)

    @classmethod
    async def regather_stream(cls, data, *, loop):
        """Used for preparing a stream, instead of downloading.
        Since Youtube Streaming links expire."""

        loop = loop or asyncio.get_event_loop()
        requester = data['requester']

        to_run = partial(ytdl.extract_info, url=data['webpage_url'], download=False)
        data = await loop.run_in_executor(None, to_run)

        return cls(discord.FFmpegPCMAudio(data['url'], **ffmpeg_options), data=data, requester=requester)


    def is_playlist(self, url):
        if self.url_source == _YOUTUBE_:
            match = re.search("list=\w+", url)
            return False if not match else True

    def get_playlist(self, url):
        try:
            # 設定 Chrome 瀏覽器的選項
            options = webdriver.ChromeOptions()
            options.add_argument("--headless") # 不開啟瀏覽器視窗

            # 建立 Chrome 瀏覽器物件
            driver = webdriver.Chrome(options=options)

            # https://www.youtube.com/watch?v=ouLndhBRL4w&list=PL1urwPG3M3NKahUbWDj_Y1qgwtRvhMpN7&index=6
            url = "https://www.youtube.com/playlist?" + url.split("&")[1]
            print(url)

            # 前往要爬取的網頁
            driver.get(url)

            # Render the dynamic content to static HTML
            html = driver.page_source
            # print(html)

            with open("html.txt", "w", encoding="utf-8") as f:
                f.write(html)

            # Parse the static HTML
            soup = BeautifulSoup(html, 'html.parser')

            # 找出所有影片連結所在的元素 by css selector
            video_links = soup.select('a.yt-simple-endpoint.style-scope.ytd-playlist-video-renderer')

            video_url = []
            # 印出每個影片的 URL
            for link in video_links:
                video_url.append('https://www.youtube.com' + link['href'])
            return video_url
        except Exception as e:
            printLog("[get_playlist][E] Unexcepted Error : %s" % e)
            return None
