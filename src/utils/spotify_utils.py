import spotipy
from discord.ext import commands
from spotipy.oauth2 import SpotifyClientCredentials

from src import config
from src.common.embeds import EmbedGenerator
from src.utils import play_utils
from src.utils import ytb_utils

eg = EmbedGenerator()

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=config.SPOTIFY_CLIENT_ID,
    client_secret=config.SPOTIFY_CLIENT_SECRET,
))


async def play_spotify(ctx: commands.Context, vc, search: str):
    try:
        if 'spotify.com/track/' in search:
            track_id = search.split('track/')[1].split('?')[0]
            await play_spotify_track(ctx, vc, track_id)
        elif 'spotify.com/playlist/' in search:
            playlist_id = search.split('playlist/')[1].split('?')[0]
            await add_tracks_from_playlist(ctx, vc, playlist_id)
        elif 'spotify.com/album/' in search:
            album_id = search.split('album/')[1].split('?')[0]
            await add_tracks_from_album(ctx, vc, album_id)
        else:
            await ctx.reply('Invalid Spotify URL')
    except Exception as e:
        await ctx.reply(f'Error processing Spotify URL: {str(e)}')


async def play_spotify_track(ctx: commands.Context, vc, track_id: str):
    try:
        track_info = sp.track(track_id)
        query = f"{track_info['name']} {track_info['artists'][0]['name']}"
        track = await ytb_utils.get_track_from_search(query)

        if not vc.is_playing():
            return await play_utils.play_track(ctx, vc, track)

        ps = play_utils.get_player_state(vc)
        ps.append_to_queue(track)
        embed = eg.song_queued(track, len(ps.queue))
        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.reply(f'Error playing Spotify track: {str(e)}')


async def add_tracks_from_playlist(ctx: commands.Context, vc, playlist_id: str):
    count = 0
    temp_msg = await ctx.send('Loading tracks...')

    try:
        results = sp.playlist_tracks(playlist_id)
        tracks = results['items']
        ps = play_utils.get_player_state(vc)

        for item in tracks:
            if item['track']:
                track_info = item['track']
                query = f"{track_info['name']} {track_info['artists'][0]['name']}"
                track = await ytb_utils.get_track_from_search(query)

                if track:
                    if not vc.is_playing():
                        await play_utils.play_track(ctx, vc, track)
                        continue

                    ps.append_to_queue(track)
                    if ps.is_queue_loop_enabled():
                        ps.append_to_loop_queue_snapshot(track)
                    count += 1

        embed = eg.playlist_added(count)
        await temp_msg.delete()
        await ctx.send(embed=embed)

    except Exception as e:
        await temp_msg.delete()
        await ctx.reply(f'Error loading playlist: {str(e)}')


async def add_tracks_from_album(ctx: commands.Context, vc, album_id: str):
    count = 0
    temp_msg = await ctx.send('Loading tracks...')

    try:
        results = sp.album_tracks(album_id)
        tracks = results['items']
        ps = play_utils.get_player_state(vc)

        for track_info in tracks:
            query = f"{track_info['name']} {track_info['artists'][0]['name']}"
            track = await ytb_utils.get_track_from_search(query)

            if track:
                if not vc.is_playing():
                    await play_utils.play_track(ctx, vc, track)
                    continue

                ps.append_to_queue(track)
                if ps.is_queue_loop_enabled():
                    ps.append_to_loop_queue_snapshot(track)
                count += 1

        embed = eg.playlist_added(count)
        await temp_msg.delete()
        await ctx.send(embed=embed)

    except Exception as e:
        await temp_msg.delete()
        await ctx.reply(f'Error loading album: {str(e)}')
