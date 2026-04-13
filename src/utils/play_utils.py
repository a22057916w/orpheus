import asyncio
import random
from typing import Optional

import discord
from discord.ext import commands

from src.common.messages import ResponseMessage as RM
from src.common.player_state import PlayerState
from src.common.track import Track
from src.common.embeds import EmbedGenerator
from src.utils import spotify_utils, ytb_utils

eg = EmbedGenerator()
PREVIOUS_TRACKS: dict[int, list[Track]] = {}
PLAYER_STATES: dict[int, PlayerState] = {}


def get_player_state(vc: discord.VoiceClient, ctx: commands.Context | None = None) -> PlayerState:
    ps = PLAYER_STATES.setdefault(vc.guild.id, PlayerState())
    if ctx is not None:
        ps.set_context(ctx)
    return ps


async def get_voice_client(ctx: commands.Context) -> Optional[discord.VoiceClient]:
    """Gets the voice client for the bot."""
    if not ctx.author.voice:
        await ctx.reply(RM.USER_NOT_IN_VOICE_CHANNEL)
        return None

    if not ctx.voice_client:
        vc = await ctx.author.voice.channel.connect()
    elif ctx.voice_client.channel != ctx.author.voice.channel:
        if not ctx.voice_client.is_playing():
            await ctx.voice_client.move_to(ctx.author.voice.channel)
            vc = ctx.voice_client
        else:
            await ctx.reply(RM.USER_NOT_IN_SAME_VOICE_CHANNEL)
            return None
    else:
        vc = ctx.voice_client

    get_player_state(vc, ctx)
    return vc


async def play(ctx: commands.Context, vc: discord.VoiceClient, search: str) -> None:
    """Resolve user input into queue items and start playback when idle."""
    try:
        if 'open.spotify' in search:
            tracks = await spotify_utils.get_tracks(search)
        else:
            tracks = await ytb_utils.get_tracks(search)
    except Exception as e:
        await ctx.reply(f'Error finding song: {str(e)}')
        return

    if not tracks:
        await ctx.reply('Could not find or load any tracks.')
        return

    ps = get_player_state(vc, ctx)

    # len(queue) before appending is where the first new track will land.
    start_index = len(ps.queue)
    
    for track in tracks:
        ps.append_to_queue(track)

    was_playing = vc.is_playing()
    if not was_playing:
        ps.set_current_index(start_index)
        await play_track(ctx, vc, tracks[0])

    if len(tracks) == 1:
        if was_playing:
            await ctx.send(embed=eg.song_queued(tracks[0], len(ps.queue)))
        return

    await ctx.send(embed=eg.playlist_added(len(tracks)))


async def play_track(ctx: commands.Context, vc: discord.VoiceClient, track: Track):
    """Play a Track."""
    ps = get_player_state(vc, ctx)

    track = await ytb_utils.resolve_track(track)
    if not track:
        await ctx.send('Could not resolve this track.')
        return

    if ps.now_playing_message:
        try:
            await ps.now_playing_message.delete()
        except:
            pass

    ps.set_current_track(track)
    ps.update_current_queue_track(track)
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
            history = PREVIOUS_TRACKS.setdefault(vc.guild.id, [])
            history.append(current_track)
            if len(history) > 10:
                history.pop(0)

        if ps.is_track_loop_enabled() and current_track:
            print('DEBUG: Replaying current track (loop mode)')
            await play_track(ps.ctx, vc, current_track)
            return

        next_track = ps.advance_to_next_track()
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


def get_history(guild_id: int) -> list[Track]:
    return PREVIOUS_TRACKS.setdefault(guild_id, [])


async def shuffle_queue(vc: discord.VoiceClient):
    ps = get_player_state(vc)
    current_index = ps.get_current_index()
    if current_index is None:
        temp = list(ps.queue)
        ps.clear_queue()
        random.shuffle(temp)
        ps.queue.extend(temp)
        return

    upcoming = list(ps.queue)[current_index + 1:]
    random.shuffle(upcoming)
    ps.queue = ps.queue.__class__(
        list(ps.queue)[:current_index + 1] + upcoming
    )

