import discord
from discord.ext import commands,tasks
import os
import youtube_dl



# Get the API token from the .env file.
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

print(DISCORD_TOKEN)

intents = discord.Intents().all()
client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix='!',intents=intents)
