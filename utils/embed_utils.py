import discord
import wavelink
import datetime
from config import PREVIOUS_TRACKS, PREFIX
from discord.ext import commands


class EmbedGenerator:
    """
    Embeds for the bot.
    """

    def __init__(self) -> None:
        pass

    def now_playing(self, song: wavelink.GenericTrack) -> discord.Embed:
        # Song(source, url, title, description, views, duration, thumbnail, channel, channel_url, False)
        embed = discord.Embed(title=f"Now Playing: {song.title} :notes:",
                              description=f"By {song.author}",
                              color=discord.Color.green())
        duration = str(datetime.timedelta(seconds=song.duration)).lstrip("0:")
        if ':' not in duration:
            duration = f'0:{duration}'
        embed.add_field(name="Duration", value=duration, inline=True)
        return embed


    def song_queued(self, song: wavelink.GenericTrack, pos: int) -> discord.Embed:
        embed = discord.Embed(title="Song Queued",
                            description=song.title,
                            color=discord.Color.blue())
        embed.add_field(name="Position", value=pos, inline=True)
        return embed


    def playlist_added(self, count: int) -> discord.Embed:
        embed = discord.Embed(title="Update Queue",
                            description=f"{count} songs were added to the queue.",
                            color=discord.Color.blue())
        return embed
