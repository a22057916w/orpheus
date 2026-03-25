import yt_dlp
from utils.play_utils import Track, play_track, play_now, disable_loops
from utils.embed_utils import EmbedGenerator
from discord.ext import commands
import config

eg = EmbedGenerator()

# yt-dlp options for audio extraction
YDL_OPTS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'extract_flat': False,
}

async def play_ytb(ctx: commands.Context, vc, search: str, now=False):
    if "list=" in search:
        if now:
            return await ctx.reply("Playnow command can only take in single songs.")
        await add_playlist(ctx, vc, search)
    else:
        await add_song(ctx, vc, search, now)

async def add_playlist(ctx: commands.Context, vc, search: str):
    """
    Adds a playlist to the queue.
    """
    try:
        with yt_dlp.YoutubeDL({'extract_flat': True, 'quiet': True}) as ydl:
            info = ydl.extract_info(search, download=False)
            if 'entries' in info:
                tracks = []
                for entry in info['entries'][:50]:  # Limit to 50 tracks
                    track = await get_track_from_url(f"https://www.youtube.com/watch?v={entry['id']}")
                    if track:
                        tracks.append(track)

                count = 0
                temp = await ctx.send('Loading tracks...')
                for track in tracks:
                    if not vc.is_playing():
                        await play_track(ctx, vc, track)
                        continue

                    vc.queue.append(track)

                    if vc.loop_all:
                        config.LOOPQ.append(track)
                    count += 1

                await temp.delete()
                await ctx.send(embed=eg.playlist_added(count))

    except Exception as e:
        await ctx.reply(f"Error loading playlist: {str(e)}")

async def add_song(ctx: commands.Context, vc, search: str, now: bool):
    """
    Adds a song to the queue or plays it
    """
    try:
        track = await get_track_from_search(search)

        if not vc.is_playing():
            return await play_track(ctx, vc, track)

        if now:
            disable_loops(vc)
            return await play_now(ctx, vc, track)

        vc.queue.append(track)
        await ctx.send(embed=eg.song_queued(track, len(vc.queue)))

        if vc.loop_all:
            config.LOOPQ.append(track)

    except Exception as e:
        await ctx.reply(f"Error finding song: {str(e)}")

async def get_track_from_search(query: str) -> Track:
    """Search YouTube and return a Track object."""
    with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
        try:
            info = ydl.extract_info(f"ytsearch:{query}", download=False)
            if 'entries' in info and info['entries']:
                entry = info['entries'][0]
                # Get the actual video URL for yt-dlp to stream
                video_url = entry.get('webpage_url', entry.get('url', ''))
                # Extract audio stream URL
                audio_info = ydl.extract_info(video_url, download=False)
                audio_url = audio_info.get('url', '')
                return Track(
                    title=entry.get('title', 'Unknown'),
                    author=entry.get('uploader', 'Unknown'),
                    url=audio_url,
                    duration=entry.get('duration', 0),
                    thumbnail=entry.get('thumbnail', '')
                )
        except Exception as e:
            raise Exception(f"Failed to search: {str(e)}")

async def get_track_from_url(url: str) -> Track:
    """Get track info from YouTube URL."""
    with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            return Track(
                title=info.get('title', 'Unknown'),
                author=info.get('uploader', 'Unknown'),
                url=info.get('url', ''),
                duration=info.get('duration', 0),
                thumbnail=info.get('thumbnail', '')
            )
        except Exception as e:
            return None
