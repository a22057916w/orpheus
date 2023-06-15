from discord.ext import commands
import wavelink


import config

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
