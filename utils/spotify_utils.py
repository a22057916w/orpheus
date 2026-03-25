import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from utils.play_utils import Track, play_track, play_now, disable_loops
from utils.embed_utils import EmbedGenerator
from utils.ytb_utils import get_track_from_search
from discord.ext import commands
import config

eg = EmbedGenerator()

# Initialize Spotify client
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=config.SPOTIFY_CLIENT_ID,
    client_secret=config.SPOTIFY_CLIENT_SECRET
))

async def play_spotify(ctx: commands.Context, vc, search: str, now=False):
    try:
        # Parse Spotify URL
        if "spotify.com/track/" in search:
            track_id = search.split("track/")[1].split("?")[0]
            await play_spotify_track(ctx, vc, track_id, now)
        elif "spotify.com/playlist/" in search:
            if now:
                return await ctx.reply("Playnow command can only take in single songs.")
            playlist_id = search.split("playlist/")[1].split("?")[0]
            await add_tracks_from_playlist(ctx, vc, playlist_id)
        elif "spotify.com/album/" in search:
            if now:
                return await ctx.reply("Playnow command can only take in single songs.")
            album_id = search.split("album/")[1].split("?")[0]
            await add_tracks_from_album(ctx, vc, album_id)
        else:
            await ctx.reply("Invalid Spotify URL")
    except Exception as e:
        await ctx.reply(f"Error processing Spotify URL: {str(e)}")

async def play_spotify_track(ctx: commands.Context, vc, track_id: str, now: bool):
    try:
        # Get track info from Spotify
        track_info = sp.track(track_id)
        query = f"{track_info['name']} {track_info['artists'][0]['name']}"

        # Search on YouTube
        track = await get_track_from_search(query)

        if not vc.is_playing():
            return await play_track(ctx, vc, track)

        if now:
            disable_loops(vc)
            return await play_now(ctx, vc, track)

        vc.queue.append(track)
        embed = eg.song_queued(track, len(vc.queue))
        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.reply(f"Error playing Spotify track: {str(e)}")

async def add_tracks_from_playlist(ctx: commands.Context, vc, playlist_id: str):
    count = 0
    temp_msg = await ctx.send('Loading tracks...')

    try:
        results = sp.playlist_tracks(playlist_id)
        tracks = results['items']

        for item in tracks:
            if item['track']:
                track_info = item['track']
                query = f"{track_info['name']} {track_info['artists'][0]['name']}"
                track = await get_track_from_search(query)

                if track:
                    if not vc.is_playing():
                        await play_track(ctx, vc, track)
                        continue

                    vc.queue.append(track)

                    if vc.loop_all:
                        config.LOOPQ.append(track)

                    count += 1

        embed = eg.playlist_added(count)
        await temp_msg.delete()
        await ctx.send(embed=embed)

    except Exception as e:
        await temp_msg.delete()
        await ctx.reply(f"Error loading playlist: {str(e)}")

async def add_tracks_from_album(ctx: commands.Context, vc, album_id: str):
    count = 0
    temp_msg = await ctx.send('Loading tracks...')

    try:
        results = sp.album_tracks(album_id)
        tracks = results['items']

        for track_info in tracks:
            query = f"{track_info['name']} {track_info['artists'][0]['name']}"
            track = await get_track_from_search(query)

            if track:
                if not vc.is_playing():
                    await play_track(ctx, vc, track)
                    continue

                vc.queue.append(track)

                if vc.loop_all:
                    config.LOOPQ.append(track)

                count += 1

        embed = eg.playlist_added(count)
        await temp_msg.delete()
        await ctx.send(embed=embed)

    except Exception as e:
        await temp_msg.delete()
        await ctx.reply(f"Error loading album: {str(e)}")
