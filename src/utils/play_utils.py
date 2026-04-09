import asyncio
import random
from typing import Optional

import discord
from discord.ext import commands

from src import config
from src.common.player_state import PlayerState
from src.common.track import Track
from src.common.embeds import EmbedGenerator

eg = EmbedGenerator()
PREVIOUS_TRACKS: list[Track] = []
PLAYER_STATES: dict[int, PlayerState] = {}


def get_player_state(vc: discord.VoiceClient, ctx: commands.Context | None = None) -> PlayerState:
    ps = PLAYER_STATES.setdefault(vc.guild.id, PlayerState())
    if ctx is not None:
        ps.set_context(ctx)
    return ps


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

    get_player_state(vc, ctx)
    return vc


async def play_track(ctx: commands.Context, vc: discord.VoiceClient, track: Track):
    """Play a Track."""
    ps = get_player_state(vc, ctx)

    if ps.now_playing_message:
        try:
            await ps.now_playing_message.delete()
        except:
            pass

    ps.set_current_track(track)
    ps.set_context(ctx)

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
    ps.now_playing_message = await ctx.send(embed=embed)


async def on_track_end(vc: discord.VoiceClient):
    """Called when a track ends."""
    try:
        ps = get_player_state(vc)
        current_track = ps.get_current_track()
        if current_track:
            PREVIOUS_TRACKS.append(current_track)
            if len(PREVIOUS_TRACKS) > 10:
                PREVIOUS_TRACKS.pop(0)

        if ps.is_track_loop_enabled() and current_track:
            print('DEBUG: Replaying current track (loop mode)')
            await play_track(ps.ctx, vc, current_track)
            return

        if ps.is_queue_loop_enabled() and not ps.queue:
            ps.restore_loop_queue_snapshot()
            print(f'DEBUG: Restored loop queue, {len(ps.queue)} tracks')

        next_track = ps.pop_next_track()
        if next_track:
            print(f'DEBUG: Playing next track from queue: {next_track.title}')
            await play_track(ps.ctx, vc, next_track)
        else:
            ps.set_current_track(None)
            print('DEBUG: Queue concluded, sending message')
            if ps.ctx:
                await ps.ctx.send('**Queue has concluded.**')
    except Exception as e:
        print(f'ERROR in on_track_end: {str(e)}')
        try:
            ps = get_player_state(vc)
            if ps.ctx:
                await ps.ctx.send(f'Error playing next track: {str(e)}')
        except:
            pass


async def play_now(ctx: commands.Context, vc: discord.VoiceClient, track: Track):
    """Plays a song immediately."""
    ps = get_player_state(vc, ctx)
    if vc.is_playing():
        vc.stop()
        current_track = ps.get_current_track()
        if current_track:
            ps.prepend_to_queue(current_track)

    ps.disable_loops()
    await play_track(ctx, vc, track)


def get_history(_guild_id: int | None = None) -> list[Track]:
    return PREVIOUS_TRACKS


async def shuffle_queue(vc: discord.VoiceClient):
    ps = get_player_state(vc)
    temp = list(ps.queue)
    ps.clear_queue()
    random.shuffle(temp)
    ps.queue.extend(temp)

