from discord.ext import commands
import discord
import asyncio
from collections import deque
from typing import Optional, Dict, Any

from utils.embed_utils import EmbedGenerator
import config

eg = EmbedGenerator()

class Track:
    """Represents a music track."""
    def __init__(self, title: str, author: str, url: str, duration: int, thumbnail: str = None):
        self.title = title
        self.author = author
        self.url = url
        self.duration = duration
        self.thumbnail = thumbnail

    def __str__(self):
        return f"{self.title} by {self.author}"

async def get_voice_client(ctx: commands.Context) -> Optional[discord.VoiceClient]:
    """Gets the voice client for the bot."""
    # Check if the user is in a voice channel.
    if not ctx.author.voice:
        await ctx.reply(config.USER_NOT_IN_VOICE_CHANNEL)
        return None

    # If bot is not in any voice channel, join the author's voice channel
    if not ctx.voice_client:
        vc = await ctx.author.voice.channel.connect()

    # If bot is in a voice channel, check if the author is in the same voice channel
    elif ctx.voice_client.channel != ctx.author.voice.channel:
        # If the bot is not playing anything, move to the author's voice channel
        if not ctx.voice_client.is_playing:
            await ctx.voice_client.move_to(ctx.author.voice.channel)
            vc = ctx.voice_client
        # If the bot is playing something, send an error message
        else:
            await ctx.reply(config.USER_NOT_IN_SAME_VOICE_CHANNEL)
            return None
    # If bot is in the same voice channel as the author, return the voice client
    else:
        vc = ctx.voice_client

    # Initialize queue and loop attributes if not present
    if not hasattr(vc, 'queue'):
        vc.queue = deque()
    if not hasattr(vc, 'loop'):
        vc.loop = False
    if not hasattr(vc, 'loop_all'):
        vc.loop_all = False
    if not hasattr(vc, 'current_track'):
        vc.current_track = None
    if not hasattr(vc, 'ctx'):
        vc.ctx = ctx

    return vc

async def play_track(ctx: commands.Context, vc: discord.VoiceClient, track: Track):
    """Play a Track."""
    if config.MESSAGE_NOW_PLAYING:
        try:
            await config.MESSAGE_NOW_PLAYING.delete()
        except:
            pass

    vc.current_track = track

    # Create FFmpeg audio source
    try:
        audio_source = discord.FFmpegPCMAudio(
            track.url,
            executable="ffmpeg",
            before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            options='-vn'
        )
        audio_source = discord.PCMVolumeTransformer(audio_source, volume=0.7)
        print(f"DEBUG: Created audio source for {track.title} ({track.url})")
    except Exception as e:
        print(f"ERROR: Failed to create audio source: {str(e)}")
        await ctx.send(f"Error creating audio source: {str(e)}")
        return

    # Play the track
    try:
        vc.play(audio_source, after=lambda e: asyncio.run_coroutine_threadsafe(
            on_track_end(vc), vc.loop
        ))
        print(f"DEBUG: Started playing {track.title}")
        print(f"DEBUG: vc.is_playing() -> {vc.is_playing()}")
    except Exception as e:
        print(f"ERROR: Failed to play track: {str(e)}")
        await ctx.send(f"Error playing track: {str(e)}")
        return

    # Send now playing embed
    embed = eg.now_playing(track)
    config.MESSAGE_NOW_PLAYING = await ctx.send(embed=embed)

    vc.ctx = ctx

async def on_track_end(vc: discord.VoiceClient):
    """Called when a track ends."""
    try:
        # Add current track to previous tracks
        if vc.current_track:
            config.PREVIOUS_TRACKS.append(vc.current_track)
            if len(config.PREVIOUS_TRACKS) > 10:
                config.PREVIOUS_TRACKS.pop(0)

        # Handle looping
        if vc.loop and vc.current_track:
            # Replay current track
            print(f"DEBUG: Replaying current track (loop mode)")
            await play_track(vc.ctx, vc, vc.current_track)
            return

        # Handle queue loop
        if vc.loop_all and not vc.queue:
            # Restore loop queue
            vc.queue = deque(config.LOOPQ) if config.LOOPQ else deque()
            print(f"DEBUG: Restored loop queue, {len(vc.queue)} tracks")

        # Play next track if queue not empty
        if vc.queue:
            next_track = vc.queue.popleft()
            print(f"DEBUG: Playing next track from queue: {next_track.title}")
            await play_track(vc.ctx, vc, next_track)
        else:
            # Queue is empty
            vc.current_track = None
            print(f"DEBUG: Queue concluded, sending message")
            await vc.ctx.send('**Queue has concluded.**')
    except Exception as e:
        print(f"ERROR in on_track_end: {str(e)}")
        try:
            await vc.ctx.send(f"Error playing next track: {str(e)}")
        except:
            pass

async def play_now(ctx: commands.Context, vc: discord.VoiceClient, track: Track):
    """Plays a song immediately."""
    if vc.is_playing():
        # Stop current track and add it back to front of queue
        vc.stop()
        if vc.current_track:
            vc.queue.appendleft(vc.current_track)

    # Disable loops for play now
    disable_loops(vc)

    # Play the new track
    await play_track(ctx, vc, track)

def get_currently_playing(vc: discord.VoiceClient) -> Optional[Track]:
    """Gets the currently playing song."""
    return vc.current_track

def disable_loops(vc: discord.VoiceClient):
    """Disables loops."""
    vc.loop = False
    vc.loop_all = False
    config.LOOPQ = None
