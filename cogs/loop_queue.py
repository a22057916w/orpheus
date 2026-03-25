from discord.ext import commands
import discord

from utils import queue_utils, play_utils
from utils.embed_utils import EmbedGenerator
import config

class LoopQ(commands.Cog):
    """
    Queue and Loop commands.
    """

    eg = EmbedGenerator()

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(aliases=['lq'])
    async def loopq(self, ctx: commands.Context):
        """Loops the queue."""
        vc = await play_utils.get_voice_client(ctx)
        if not vc:
            return

        # If the bot is not playing anything, return.
        if not vc.is_playing:
            return await ctx.send('I am not playing anything.')

        # If the song is on loop, turn it off.
        if vc.loop_all:
            vc.loop_all = False
            config.LOOPQ = None
            await ctx.send('*Loop disabled*')
        # If the song is not on loop, turn it on.
        else:
            vc.loop_all = True
            current_track = play_utils.get_currently_playing(vc)
            config.LOOPQ = list(vc.queue)  # Copy current queue
            if current_track:
                config.LOOPQ.insert(0, current_track)  # Add current track to front
            await ctx.send('**Queue is now on loop :repeat:**')

    @commands.command(aliases=['l'])
    async def loop(self, ctx: commands.Context):
        """Loops the current song."""
        vc = await play_utils.get_voice_client(ctx)
        if not vc:
            return

        # If the bot is not playing anything, return.
        if not vc.is_playing:
            return await ctx.send('I am not playing anything.')

        # If the song is on loop, turn it off.
        if vc.loop:
            vc.loop = False
            await ctx.send('**Loop disabled**')
        # If the song is not on loop, turn it on.
        else:
            vc.loop = True
            current_track = play_utils.get_currently_playing(vc)
            await ctx.send(f'**Looping {current_track.title}:repeat:**')

async def setup(bot: commands.Bot):
    await bot.add_cog(LoopQ(bot))
