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

        ps = play_utils.get_player_state(vc)
        if ps.is_queue_loop_enabled():
            ps.set_queue_loop(False)
            ps.set_loop_queue_snapshot([])
            await ctx.send('*Loop disabled*')
        else:
            ps.set_queue_loop(True)
            snapshot = list(ps.queue)
            current_track = ps.get_current_track()
            if current_track:
                snapshot.insert(0, current_track)
            ps.set_loop_queue_snapshot(snapshot)
            await ctx.send('**Queue is now on loop :repeat:**')

    @commands.command(aliases=['l'])
    async def loop(self, ctx: commands.Context):
        """Loops the current song."""
        vc = await play_utils.get_voice_client(ctx)
        if not vc:
            return

        if not vc.is_playing:
            return await ctx.send('I am not playing anything.')

        ps = play_utils.get_player_state(vc)
        if ps.is_track_loop_enabled():
            ps.set_track_loop(False)
            await ctx.send('**Loop disabled**')
        else:
            ps.set_track_loop(True)
            current_track = ps.get_current_track()
            await ctx.send(f'**Looping {current_track.title}:repeat:**')


async def setup(bot: commands.Bot):
    await bot.add_cog(LoopQ(bot))
