import asyncio
import random
from collections import deque
from typing import Optional

import discord
from discord.ext import commands

from src import config
from src.domain.track import Track
from src.presentation.embed_utils import EmbedGenerator

eg = EmbedGenerator()
MESSAGE_NOW_PLAYING = None
PREVIOUS_TRACKS: list[Track] = []


async def get_voice_client(ctx: commands.Context) -> Optional[discord.VoiceClient]:
    """Gets the voice client for the bot."""
    if not ctx.author.voice:
        await ctx.reply(config.USER_NOT_IN_VOICE_CHANNEL)
        return None

    if not ctx.voice_client:
        vc = await ctx.author.voice.channel.connect()
    elif ctx.voice_client.channel != ctx.author.voice.channel:
        if not ctx.voice_client.is_playing:
            await ctx.voice_client.move_to(ctx.author.voice.channel)
            vc = ctx.voice_client
        else:
            await ctx.reply(config.USER_NOT_IN_SAME_VOICE_CHANNEL)
            return None
    else:
        vc = ctx.voice_client

    if not hasattr(vc, 'queue'):
        vc.queue = deque()
    if not hasattr(vc, 'track_loop'):
        vc.track_loop = False
    if not hasattr(vc, 'loop_all'):
        vc.loop_all = False
    if not hasattr(vc, 'current_track'):
        vc.current_track = None
    if not hasattr(vc, 'ctx'):
        vc.ctx = ctx
    if not hasattr(vc, 'loop_queue_snapshot'):
        vc.loop_queue_snapshot = []

    vc.ctx = ctx
    return vc


async def play_track(ctx: commands.Context, vc: discord.VoiceClient, track: Track):
    """Play a Track."""
    global MESSAGE_NOW_PLAYING

    if MESSAGE_NOW_PLAYING:
        try:
            await MESSAGE_NOW_PLAYING.delete()
        except:
            pass

    vc.current_track = track
    vc.ctx = ctx

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

    try:
        vc.play(audio_source, after=lambda e: asyncio.run_coroutine_threadsafe(
            on_track_end(vc), vc.client.loop
        ))
        print(f"DEBUG: Started playing {track.title}")
        print(f"DEBUG: vc.is_playing() -> {vc.is_playing()}")
    except Exception as e:
        print(f"ERROR: Failed to play track: {str(e)}")
        await ctx.send(f"Error playing track: {str(e)}")
        return

    embed = eg.now_playing(track)
    MESSAGE_NOW_PLAYING = await ctx.send(embed=embed)


async def on_track_end(vc: discord.VoiceClient):
    """Called when a track ends."""
    try:
        if vc.current_track:
            PREVIOUS_TRACKS.append(vc.current_track)
            if len(PREVIOUS_TRACKS) > 10:
                PREVIOUS_TRACKS.pop(0)

        if vc.track_loop and vc.current_track:
            print('DEBUG: Replaying current track (loop mode)')
            await play_track(vc.ctx, vc, vc.current_track)
            return

        if vc.loop_all and not vc.queue:
            vc.queue = deque(vc.loop_queue_snapshot)
            print(f'DEBUG: Restored loop queue, {len(vc.queue)} tracks')

        if vc.queue:
            next_track = vc.queue.popleft()
            print(f'DEBUG: Playing next track from queue: {next_track.title}')
            await play_track(vc.ctx, vc, next_track)
        else:
            vc.current_track = None
            print('DEBUG: Queue concluded, sending message')
            if vc.ctx:
                await vc.ctx.send('**Queue has concluded.**')
    except Exception as e:
        print(f'ERROR in on_track_end: {str(e)}')
        try:
            if vc.ctx:
                await vc.ctx.send(f'Error playing next track: {str(e)}')
        except:
            pass


async def play_now(ctx: commands.Context, vc: discord.VoiceClient, track: Track):
    """Plays a song immediately."""
    if vc.is_playing():
        vc.stop()
        if vc.current_track:
            vc.queue.appendleft(vc.current_track)

    disable_loops(vc)
    await play_track(ctx, vc, track)


def get_currently_playing(vc: discord.VoiceClient) -> Optional[Track]:
    return vc.current_track


def get_queue(vc: discord.VoiceClient):
    return vc.queue


def get_history(_guild_id: int | None = None) -> list[Track]:
    return PREVIOUS_TRACKS


async def shuffle_queue(vc: discord.VoiceClient):
    temp = list(vc.queue)
    vc.queue.clear()
    random.shuffle(temp)
    vc.queue.extend(temp)


def disable_loops(vc: discord.VoiceClient):
    vc.track_loop = False
    vc.loop_all = False
    vc.loop_queue_snapshot = []
