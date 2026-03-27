import asyncio
from typing import override
import discord
from discord.ext import commands
import os
import config

DISCORD_TOKEN = config.DISCORD_TOKEN

class Bot(commands.Bot):
    """
    The main bot class. Inherits from commands.Bot, which itself inherits from discord.Client.
    This class is responsible for initializing the bot, loading cogs, and handling events.
    """
    def __init__(self) -> None:
        # Enable only the intents the bot currently needs.
        intents = discord.Intents.default()
        intents.guilds = True
        intents.voice_states = True
        intents.message_content = True

        super().__init__(intents=intents, command_prefix='!')

    # discord.py calls this hook automatically during startup for async initialization.
    @override
    async def setup_hook(self) -> None:
        await self.load_cogs()

    @override 
    async def on_ready(self) -> None:
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name="!help"
            )
        )
        print(f'Bot is ready! Logged in as {self.user}')

    async def load_cogs(self) -> None:
        for pyfile in sorted(os.listdir("./cogs")):
            if pyfile.endswith(".py") and pyfile != "__init__.py":
                await self.load_extension(f'cogs.{pyfile[:-3]}')
                print(f'Load module {pyfile[:-3]} successfully')

async def main() -> None:
    if not DISCORD_TOKEN:
        raise RuntimeError("DISCORD_TOKEN is missing. Check your .env or environment variables.")

    bot = Bot()
    async with bot:
        await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
