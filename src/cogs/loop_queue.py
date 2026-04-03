from discord.ext import commands

from src.common.embeds import EmbedGenerator
from src.utils import play_utils


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

        if not vc.is_playing:
            return await ctx.send('I am not playing anything.')

        if vc.loop_all:
            vc.loop_all = False
            vc.loop_queue_snapshot = []
            await ctx.send('*Loop disabled*')
        else:
            vc.loop_all = True
            current_track = play_utils.get_currently_playing(vc)
            vc.loop_queue_snapshot = list(play_utils.get_queue(vc))
            if current_track:
                vc.loop_queue_snapshot.insert(0, current_track)
            await ctx.send('**Queue is now on loop :repeat:**')

    @commands.command(aliases=['l'])
    async def loop(self, ctx: commands.Context):
        """Loops the current song."""
        vc = await play_utils.get_voice_client(ctx)
        if not vc:
            return

        if not vc.is_playing:
            return await ctx.send('I am not playing anything.')

        if vc.track_loop:
            vc.track_loop = False
            await ctx.send('**Loop disabled**')
        else:
            vc.track_loop = True
            current_track = play_utils.get_currently_playing(vc)
            await ctx.send(f'**Looping {current_track.title}:repeat:**')


async def setup(bot: commands.Bot):
    await bot.add_cog(LoopQ(bot))
