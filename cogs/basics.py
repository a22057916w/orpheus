from discord.ext import commands

class Basics(commands.Cog):
    """Basic commands for the bot."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx: commands.Context):
        """Returns the bot's latency in milliseconds."""
        await ctx.reply(f'*Pong! {round(self.bot.latency * 1000)}ms*')

    @commands.command()
    async def reload(self, ctx, extension):
        "Reload a specific cog."
        async with ctx.typing():
            self.bot.reload_extension(f'cogs.{extension}')
            print(f'Reload module {extension} successfully')
        await ctx.send(f'Reload module {extension} successfully')

async def setup(bot: commands.Bot):
    await bot.add_cog(Basics(bot))
