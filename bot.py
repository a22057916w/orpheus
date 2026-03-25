import discord
from discord.ext import commands
import os
import config

# Get the API token from the .env file.
DISCORD_TOKEN = config.DISCORD_TOKEN

class Bot(commands.Bot):
    def __init__(self) -> None:
        # contain bot features, like type, message, guild
        intents = discord.Intents.all()
        intents.message_content = True

        # connect to discord server and init bot command features
        super().__init__(intents=intents, command_prefix='!')

    async def on_ready(self) -> None:
        await self.load_cog()
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="!help"))
        print(f'Bot is ready! Logged in as {self.user}')

    async def load_cog(self):
        for pyfile in os.listdir("./cogs"):
            if pyfile.endswith(".py"):
                await self.load_extension(f'cogs.{pyfile[:-3]}')
                print(f'Load module {pyfile[:-3]} successfully')

if __name__ == "__main__":
    bot = Bot()
    bot.run(DISCORD_TOKEN)
