from discord.ext import commands
import discord

from src.presentation.embed_utils import EmbedGenerator
from src.utils import play_utils
from src.utils import spotify_utils, ytb_utils


class Player(commands.Cog):
    eg = EmbedGenerator()

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """Disconnects the bot when the last person leaves the voice channel."""
        if member.guild.voice_client not in self.bot.voice_clients:
            return

        if before.channel == after.channel:
            return

        if not before.channel:
            return

        if member == self.bot.user and not after.channel:
            vc = member.guild.voice_client
            await vc.disconnect()
            return

        if len(before.channel.members) == 1 and before.channel.members[0] == self.bot.user:
            vc = member.guild.voice_client
            await vc.disconnect()
            return

    @commands.command(aliases=['p'])
    async def play(self, ctx: commands.Context, *, search):
        """Plays a song."""
        if not search:
            await ctx.reply('Please enter a search query.')
            return

        vc = await play_utils.get_voice_client(ctx)
        if not vc:
            return

        if 'open.spotify' in search:
            await spotify_utils.play_spotify(ctx, vc, search)
        else:
            await ytb_utils.play_ytb(ctx, vc, search)

    @commands.command(aliases=['pn'])
    async def playnow(self, ctx: commands.Context, *, search):
        """Plays a song now."""
        if not search:
            await ctx.reply('Please enter a search query.')
            return

        vc = await play_utils.get_voice_client(ctx)
        if not vc:
            return

        if 'open.spotify' in search:
            await spotify_utils.play_spotify(ctx, vc, search, now=True)
        else:
            await ytb_utils.play_ytb(ctx, vc, search, now=True)

    @commands.command()
    async def join(self, ctx: commands.Context):
        """Joins a voice channel."""
        return await play_utils.get_voice_client(ctx)

    @commands.command(aliases=['disconnect'])
    async def leave(self, ctx: commands.Context):
        """Leaves a voice channel."""
        vc = await play_utils.get_voice_client(ctx)
        if not vc:
            return
        await vc.disconnect()

    @commands.command()
    async def pause(self, ctx: commands.Context):
        """Pauses the current song."""
        vc = await play_utils.get_voice_client(ctx)
        if not vc:
            return

        if not vc.is_playing:
            return await ctx.send('I am not playing anything.')

        vc.pause()
        await ctx.send('**Paused**')

    @commands.command(aliases=['res', 'r'])
    async def resume(self, ctx: commands.Context):
        """Resumes the current song."""
        vc = await play_utils.get_voice_client(ctx)
        if vc:
            vc.resume()
            await ctx.send('**Resumed**')

    @commands.command(aliases=['np'])
    async def now_playing(self, ctx: commands.Context):
        """Shows the current song."""
        vc = await play_utils.get_voice_client(ctx)
        if not vc:
            return

        if not vc.is_playing:
            return await ctx.send('I am not playing anything.')

        await ctx.send(embed=self.eg.now_playing(play_utils.get_currently_playing(vc)))

    @commands.command()
    async def skip(self, ctx: commands.Context):
        """Skips the current song."""
        vc = await play_utils.get_voice_client(ctx)
        if not vc:
            return

        if not vc.is_playing:
            return await ctx.send('I am not playing anything.')

        track = play_utils.get_currently_playing(vc)
        vc.stop()
        await ctx.send(f'*Skipped* **{track.title}**')

    @commands.command(aliases=['st'])
    async def skipto(self, ctx: commands.Context, pos: int = False):
        """Skips to a position in the queue."""
        if not pos:
            return await ctx.reply('Please enter a position.')

        vc = await play_utils.get_voice_client(ctx)
        if not vc:
            return

        queue = play_utils.get_queue(vc)
        if not queue:
            return await ctx.reply('*Queue is empty*')

        if pos > len(queue) or pos <= 0:
            return await ctx.reply(f'Position should be between 0 and {len(queue)}')

        for _ in range(pos - 1):
            if queue:
                queue.popleft()

        if vc.is_playing:
            vc.stop()

        if queue:
            next_track = queue.popleft()
            await play_utils.play_track(ctx, vc, next_track)

        await ctx.reply(f'**Skipped to position {pos}**')

    @commands.command()
    async def stop(self, ctx: commands.Context):
        """Stops the current song."""
        vc = await play_utils.get_voice_client(ctx)
        if not vc:
            return

        if not vc.is_playing:
            return await ctx.send('I am not playing anything.')

        play_utils.get_queue(vc).clear()
        play_utils.disable_loops(vc)
        vc.stop()
        await ctx.send('**Stopped**')

    @commands.command(name='recentlyplayed', aliases=['sp', 'rp', 'showprevious'])
    async def previous(self, ctx: commands.Context):
        """Shows the recently played songs."""
        history = play_utils.get_history(ctx.guild.id)
        if not history:
            await ctx.reply('Nothing has been played yet')
            return
        await ctx.send(embed=self.eg.show_previous(history))

    @commands.command(name='playlast', aliases=['pl'])
    async def play_last(self, ctx: commands.Context, pos: int = 1):
        """Plays the selected song from recently played songs."""
        history = play_utils.get_history(ctx.guild.id)
        if not history:
            await ctx.reply('Nothing has been played yet')
            return

        vc = await play_utils.get_voice_client(ctx)
        if not vc:
            return

        if pos > len(history) or pos <= 0:
            await ctx.reply(f'Position should be between 1 and {len(history)}')
            return

        track = history.pop(pos - 1)
        await self.playnow(ctx, search=track.url)

    @commands.command(aliases=['rem'])
    async def remove(self, ctx: commands.Context, pos: int = False):
        """Removes a song from the queue."""
        if not pos:
            return await ctx.reply('Please provide a position.')

        vc = await play_utils.get_voice_client(ctx)
        if not vc:
            return

        queue = play_utils.get_queue(vc)
        if not queue:
            return await ctx.reply('*Queue is empty*')

        if pos > len(queue) or pos <= 0:
            return await ctx.reply(f'Position should be between 1 and {len(queue)}')

        track = queue[pos - 1]
        del queue[pos - 1]
        await ctx.reply(f'Removed **{track.title}** from the queue.')

    @commands.command()
    async def search(self, ctx: commands.Context, *, title: str = ''):
        """Searches for a song in the queue using the given keywords."""
        if not title:
            await ctx.reply('Please enter a title.')

        vc = await play_utils.get_voice_client(ctx)
        if not vc:
            return

        words = [word for word in title.split(' ') if word not in ['the', 'a', 'an']]
        queue = play_utils.get_queue(vc)

        for i in range(len(queue)):
            for word in words:
                if word.lower() not in queue[i].title.lower():
                    break
            else:
                await ctx.reply(f'**{queue[i].title}** is at position {i+1}')
                return

        await ctx.reply(f'No song found with the title **{title}**')

    @commands.command()
    async def move(self, ctx: commands.Context, pos: int = -1, new_pos: int = -1):
        """Moves a song from one position to another."""
        if pos == -1 or new_pos == -1:
            return await ctx.reply('Please enter a position.')

        vc = await play_utils.get_voice_client(ctx)
        if not vc:
            return

        queue = play_utils.get_queue(vc)
        if not queue:
            return await ctx.reply('*Queue is empty*')

        if pos > len(queue) or pos <= 0 or new_pos > len(queue) or new_pos <= 0:
            return await ctx.reply(f'Positions should be between 1 and {len(queue)}')

        track = queue[pos - 1]
        if pos == new_pos:
            return await ctx.reply(f'**{track.title}** is already at position {pos}.')

        del queue[pos - 1]
        queue.insert(new_pos - 1, track)
        await ctx.reply(f'Moved **{track.title}** to position {new_pos}.')


async def setup(bot: commands.Bot):
    await bot.add_cog(Player(bot))
