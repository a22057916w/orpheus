import discord
from discord.ext import commands,tasks
import os
import youtube_dl



# Get the API token from the .env file.
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

#print(DISCORD_TOKEN)

intents = discord.Intents().default()                       # contain bot features, like type, message, guild
client = discord.Client(intents=intents)                # connect to discord server
bot = commands.Bot(command_prefix='!',intents=intents)  # init bot command features


youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
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

# ???
ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

# If you turn up Master volume, everything gets louder...headphones, CD, etc. PCM turns up the volume just for sound files,
# but CD volume would remain the same. Useful if you'd like MP3's to be louder than audio CD's.
class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)                # Transforms a previous "AudioSource" to have volume controls. 
        self.data = data
        self.title = data.get('title')
        self.url = ""

    # The method takes in the URL as a parameter and returns the filename of the audio file which gets downloaded.
    @classmethod    # 一般函數的第一個參數指的是該物件的記憶體位置，classmethod的第一個參數指的是該類別的記憶體位置。用法類似static method
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]
        filename = data['title'] if stream else ytdl.prepare_filename(data)
        return filename


# add the join() method to tell the bot to join the voice channel and the leave() method to tell the bot to disconnect
@bot.command(name='join', help='Tells the bot to join the voice channel')
async def join(ctx):
    if not ctx.message.author.voice:        # ctx是一種引數，且ctx是context(上下文的縮寫) author是本人(dircord user)
        await ctx.send("{} is not connected to a voice channel".format(ctx.message.author.name))
        return
    else:
        channel = ctx.message.author.voice.channel
    await channel.connect()

@bot.command(name='leave', help='To make the bot leave the voice channel')
async def leave(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_connected():
        await voice_client.disconnect()
    else:
        await ctx.send("The bot is not connected to a voice channel.")


# add the following methods: play(), pause(), resume(),stop()
@bot.command(name='play_song', help='To play song')
async def play(ctx,url):
    try :
        server = ctx.message.guild
        voice_channel = server.voice_client

        async with ctx.typing():
            filename = await YTDLSource.from_url(url, loop=bot.loop)
            voice_channel.play(discord.FFmpegPCMAudio(executable="ffmpeg.exe", source=filename))
        await ctx.send('**Now playing:** {}'.format(filename))
    except:
        await ctx.send("The bot is not connected to a voice channel.")


@bot.command(name='pause', help='This command pauses the song')
async def pause(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_playing():
        await voice_client.pause()
    else:
        await ctx.send("The bot is not playing anything at the moment.")

@bot.command(name='resume', help='Resumes the song')
async def resume(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_paused():
        await voice_client.resume()
    else:
        await ctx.send("The bot was not playing anything before this. Use play_song command")

@bot.command(name='stop', help='Stops the song')
async def stop(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_playing():
        await voice_client.stop()
    else:
        await ctx.send("The bot is not playing anything at the moment.")


#調用event函式庫
@bot.event
#當機器人完成啟動時
async def on_ready():
    print('目前登入身份：',bot.user)

if __name__ == "__main__" :
    bot.run(DISCORD_TOKEN)
