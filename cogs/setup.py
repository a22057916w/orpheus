from discord.ext import commands
import discord
import wavelink
from wavelink.ext import spotify
# from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET_ID, PREFIX

class Setup(commands.Cog):
    """
    Basic commands for the bot.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        print(f'Logged in {self.user} | {self.user.id}')

    @commands.Cog.listener()
    async def on_wavelink_node_ready(node: wavelink.Node):
        print(f'Node {node.identifier} is ready!')

    async def setup_hook(self) -> None:
        # Wavelink 2.0 has made connecting Nodes easier... Simply create each Node
        # and pass it to NodePool.connect with the client/bot.
        # Fill your Spotify API details and pass it to connect.
        sc = spotify.SpotifyClient(
            client_id='6d793485170f46749e32ce46ad3da004',
            client_secret='214b8f17a448431a8ca1bde6c25e72be'
        )
        node: wavelink.Node = wavelink.Node(uri='http://localhost:2333', password='youshallnotpass')
        await wavelink.NodePool.connect(client=self, nodes=[node], spotify=sc)


async def setup(bot):
    await bot.add_cog(Setup(bot))
