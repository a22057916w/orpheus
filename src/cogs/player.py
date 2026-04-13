from discord.ext import commands
import discord

from src.common.embeds import EmbedGenerator
from src.utils import play_utils


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

        await play_utils.play(ctx, vc, search)

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

        if not vc.is_playing():
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

        if not vc.is_playing():
            return await ctx.send('I am not playing anything.')

        ps = play_utils.get_player_state(vc)
        await ctx.send(embed=self.eg.now_playing(ps.get_current_track()))

    @commands.command()
    async def skip(self, ctx: commands.Context):
        """Skips the current song."""
        vc = await play_utils.get_voice_client(ctx)
        if not vc:
            return

        if not vc.is_playing():
            return await ctx.send('I am not playing anything.')

        ps = play_utils.get_player_state(vc)
        track = ps.get_current_track()
        vc.stop()
        await ctx.send(f'*Skipped* **{track.title}**')

    @commands.command(aliases=['l', 'loopq', 'lq'])
    async def loop(self, ctx: commands.Context):
        """Cycles between queue loop, song loop, and loop off."""
        vc = await play_utils.get_voice_client(ctx)
        if not vc:
            return

        if not vc.is_playing():
            return await ctx.send('I am not playing anything.')

        ps = play_utils.get_player_state(vc)
        if not ps.is_queue_loop_enabled() and not ps.is_track_loop_enabled():
            ps.set_queue_loop(True)
            ps.set_track_loop(False)
            await ctx.send('**Queue is now on loop :repeat:**')
        elif ps.is_queue_loop_enabled():
            ps.set_queue_loop(False)
            ps.set_track_loop(True)
            current_track = ps.get_current_track()
            await ctx.send(f'**Looping {current_track.title}:repeat:**')
        else:
            ps.disable_loops()
            await ctx.send('**Loop disabled**')

    @commands.command()
    async def stop(self, ctx: commands.Context):
        """Stops the current song."""
        vc = await play_utils.get_voice_client(ctx)
        if not vc:
            return

        if not vc.is_playing():
            return await ctx.send('I am not playing anything.')

        ps = play_utils.get_player_state(vc)
        ps.clear_queue()
        ps.disable_loops()
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
        ps = play_utils.get_player_state(vc)
        start_index = len(ps.queue)
        ps.append_to_queue(track)
        if not vc.is_playing():
            ps.set_current_index(start_index)
            await play_utils.play_track(ctx, vc, track)
            return

        await ctx.send(embed=self.eg.song_queued(track, len(ps.queue)))

    @commands.command(aliases=['rem'])
    async def remove(self, ctx: commands.Context, pos: int = False):
        """Removes a song from the queue."""
        if not pos:
            return await ctx.reply('Please provide a position.')

        vc = await play_utils.get_voice_client(ctx)
        if not vc:
            return

        ps = play_utils.get_player_state(vc)
        queue = ps.queue
        if not queue:
            return await ctx.reply('*Queue is empty*')

        if pos > len(queue) or pos <= 0:
            return await ctx.reply(f'Position should be between 1 and {len(queue)}')

        removed_index = pos - 1
        was_current = ps.get_current_index() == removed_index
        track = ps.remove_from_queue(removed_index)
        if was_current:
            ps.set_track_loop(False)
            if vc.is_playing():
                vc.stop()
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
        queue = play_utils.get_player_state(vc).queue

        for i in range(len(queue)):
            for word in words:
                if word.lower() not in queue[i].title.lower():
                    break
            else:
                await ctx.reply(f'**{queue[i].title}** is at position {i+1}')
                return

        await ctx.reply(f'No song found with the title **{title}**')


async def setup(bot: commands.Bot):
    await bot.add_cog(Player(bot))
