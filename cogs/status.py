import discord
from discord.ext import commands,tasks

import os
import asyncio

class Status(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def update_status(self, ctx):
        await self.bot.change_presence(activity=discord.CustomActivity(name='Fuck this shit' ,emoji='🖥️'))


def setup(bot):
    bot.add_cog(Status(bot))
