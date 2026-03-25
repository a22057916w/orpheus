import discord
import datetime
from typing import Any
from config import PREVIOUS_TRACKS, PREFIX
from discord.ext import commands


class EmbedGenerator:
    """
    Embeds for the bot.
    """

    def __init__(self) -> None:
        pass

    def now_playing(self, song: Any) -> discord.Embed:
        embed = discord.Embed(title=f"Now Playing: {song.title} :notes:",
                              description=f"By {song.author}",
                              color=discord.Color.green())
        duration = str(datetime.timedelta(seconds=song.duration)).lstrip("0:")
        if ':' not in duration:
            duration = f'0:{duration}'
        embed.add_field(name="Duration", value=duration, inline=True)
        return embed


    def song_queued(self, song: Any, pos: int) -> discord.Embed:
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

    def show_queue(self, vc: discord.VoiceClient) -> list[discord.Embed]:
        pages = []
        songs = list(vc.queue)
        song_count = 0
        desc = ""
        total_songs = len(songs)
        page_count = 1

        for song in songs:
            song_count += 1
            try:
                duration = str(datetime.timedelta(seconds=song.duration)).lstrip("0:")
                if ':' not in duration:
                    duration = f'0:{duration}'

                desc += f"{song_count}. {song.title}[{duration}]\n"

            except AttributeError:
                desc += f"{song_count}. {song.title}\n"

            if song_count % 15 == 0 and song_count // 15 == page_count:
                queue_embed_page = discord.Embed(
                    title=f"Queue | {total_songs} Tracks",
                    description=desc,
                    color=discord.Color.gold()
                )
                pages.append(queue_embed_page)
                desc = ""
                page_count += 1

        if desc:
            queue_embed_page = discord.Embed(
                title=f"Queue | {total_songs} Tracks",
                description=desc,
                color=discord.Color.gold())
            pages.append(queue_embed_page)

        return pages


    def show_previous(self):
        desc=""
        song_count = 0
        for track in PREVIOUS_TRACKS:
            song_count += 1
            try:
                duration = str(datetime.timedelta(seconds=track.duration)).lstrip("0:")
                if ':' not in duration:
                    duration = f'0:{duration}'

                desc += f"{song_count}. {track.title}[{duration}]\n"

            except AttributeError:
                desc += f"{song_count}. {track.title}\n"

        embed = discord.Embed(
            title=f"Recently Played | {len(PREVIOUS_TRACKS)} Tracks",
            description=desc,
            color=discord.Color.brand_red())
        return embed
