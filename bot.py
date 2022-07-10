import discord
from discord.ext import commands,tasks

import os

# contain bot features, like type, message, guild
intents = discord.Intents().default()
# connect to discord server and init bot command features
bot = commands.Bot(command_prefix="!", intents=intents)
# Get the API token from the .env file.
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

@bot.command()
async def load(ctx, extension):
    # the extension name to load. It must be dot separated like regular Python imports if accessing a sub-module.
    # e.g. foo.test if you want to import foo/test.py.
    bot.load_extension(f'cogs.{extension}')
    print(f'Load module {extension} successfully')

@bot.command()
async def unload(ctx, extension):
    bot.unload_extension(f'cogs.{extension}')
    print(f'Unload module {extension} successfully')

@bot.command()
async def reload(ctx, extension):
    async with ctx.typing():
        bot.reload_extension(f'cogs.{extension}')
        print(f'Reload module {extension} successfully')
    await ctx.send(f'Reload module {extension} successfully')

# 當機器人完成啟動時
@bot.event
async def on_ready():
    print('目前登入身份：', bot.user)

if __name__ == "__main__":
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            bot.load_extension(f'cogs.{filename[:-3]}')
            print(f'Load moduel {filename[:-3]} successfully')

    bot.run(DISCORD_TOKEN)
