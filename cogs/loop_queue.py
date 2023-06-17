from discord.ext import commands
import wavelink
from utils import queue_utils, play_utils
import config
from utils.embed_util import EmbedGenerator
import Paginator

class LoopQ(commands.Cog):
    """"
    Queue and Loop commands.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, player: wavelink.Player, track: wavelink.GenericTrack, reason):
        """
        Listens for when a track ends.
        """
        ctx = player.ctx
        vc = player.guild.voice_client

        # If the track is on loop, play it again.
        if vc.loop:
            return await play_utils.play_track(ctx, vc, track)

        # Add the song to history
        queue_utils.add_to_previous_queue(track)

        # If the queue is not empty, play the next song.
        if not vc.queue.is_empty:
            next_song = vc.queue.get()
            await play_utils.play_track(ctx, vc, next_song)

        elif vc.loopq:
            vc.queue = config.LOOPQ.copy()
            next_song = vc.queue.get()
            await play_utils.play_track(ctx, vc, next_song)

        # If the queue is empty, stop the player.
        else:
            await vc.stop()
            await ctx.send('**Queue has concluded.**')


async def setup(bot: commands.Bot):
    await bot.add_cog(LoopQ(bot))
