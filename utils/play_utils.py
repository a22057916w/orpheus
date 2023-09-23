from discord.ext import commands
import wavelink

from utils.embed_utils import EmbedGenerator
import config

eg = EmbedGenerator()

async def get_voice_client(ctx: commands.Context) -> wavelink.Player or None:
    """Gets the voice client for the bot."""
    # Check if the user is in a voice channel.
    if not ctx.author.voice:
        await ctx.reply(config.USER_NOT_IN_VOICE_CHANNEL)
        return None

    # If bot is not in any voice channel, join the author's voice channel
    if not ctx.voice_client:
        vc: wavelink.Player = await ctx.author.voice.channel.connect(cls=wavelink.Player)

    # If bot is in a voice channel, check if the author is in the same voice channel
    elif ctx.voice_client.channel != ctx.author.voice.channel:
        # If the bot is not playing anything, move to the author's voice channel
        if not ctx.voice_client.is_playing:
            await ctx.voice_client.move_to(ctx.author.voice.channel)
            vc: wavelink.Player = ctx.voice_client
        # If the bot is playing something, send an error message
        else:
            await ctx.reply(config.USER_NOT_IN_SAME_VOICE_CHANNEL)
            return None
    # If bot is in the same voice channel as the author, return the voice client
    else:
        vc: wavelink.Player = ctx.voice_client

    return vc

async def play_track(ctx: commands.Context, vc: wavelink.Player, track: wavelink.GenericTrack):
    """ Play a Track. """
    if config.MESSAGE_NOW_PLAYING:
        await config.MESSAGE_NOW_PLAYING.delete()

    track = track[0]
    await vc.play(track)

    # wavelink gets song from ytb and eventually convert to YoutbeTrack,
    # hence the embed must place after vc.play
    embed = eg.now_playing(vc.current)
    config.MESSAGE_NOW_PLAYING = await ctx.send(embed=embed)

    vc.ctx = ctx
    if not hasattr(vc, 'loop'):
        vc.loop = False
    if not hasattr(vc, 'loopq'):
        vc.loopq = False


async def play_now(ctx: commands.Context, vc: wavelink.Player, track: wavelink.GenericTrack):
    """Plays a song immediately."""
    if not vc.is_playing:
        await play_track(ctx, vc, track)
        return

    current_track = get_currenly_playing(vc)

    # Adds the reqire song to the front of queue and skips the current song
    vc.queue.put_at_front(track)

    await vc.stop()

    # put the current song after the require song
    await vc.queue.put_wait(current_track)

    await play_track(ctx, vc, track)

def get_currenly_playing(vc: wavelink.Player) -> wavelink.GenericTrack:
    """Gets the currently playing song."""
    return vc.current

def disable_loops(vc: wavelink.Player):
    """Disables loops."""
    vc.loop = False
    vc.loopq = False
    config.LOOPQ = None
