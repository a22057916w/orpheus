import discord
from discord.ext import commands,tasks

import wavelink
from wavelink.ext import spotify

import os

# contain bot features, like type, message, guild
# intents = discord.Intents.all()
# intents.message_content = True
# # connect to discord server and init bot command features
# bot = commands.Bot(command_prefix="!", intents=intents)
# # Get the API token from the .env file.
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

class Bot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.all()
        intents.message_content = True
        super().__init__(intents=intents, command_prefix='!')

    async def on_ready(self) -> None:
        await self.load_cog()
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="!help"))
        print(f'Bot is ready! Logged in as {self.user}')

    async def load_cog(self):
        for pyfile in os.listdir("./cogs"):
            if pyfile.endswith(".py"):
                await bot.load_extension(f'cogs.{pyfile[:-3]}')
                print(f'Load moduel {pyfile[:-3]} successfully')

    async def setup_hook(self) -> None:
        # Wavelink 2.0 has made connecting Nodes easier... Simply create each Node
        # and pass it to NodePool.connect with the client/bot.
        # Fill your Spotify API details and pass it to connect.
        sc = spotify.SpotifyClient(
            client_id='6d793485170f46749e32ce46ad3da004',
            client_secret='214b8f17a448431a8ca1bde6c25e72be'
        )
        node: wavelink.Node = wavelink.Node(uri='http://127.0.0.1:2333', password='youshallnotpass')
        await wavelink.NodePool.connect(client=self, nodes=[node], spotify=sc)




if __name__ == "__main__":
    bot = Bot()

    # @bot.command()
    # async def reload(self, ctx, extension):
    #     async with ctx.typing():
    #         bot.reload_extension(f'cogs.{extension}')
    #         print(f'Reload module {extension} successfully')
    #     await ctx.send(f'Reload module {extension} successfully')

    bot.run(DISCORD_TOKEN)
