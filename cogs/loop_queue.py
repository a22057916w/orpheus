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


async def setup(bot: commands.Bot):
    await bot.add_cog(LoopQ(bot))
