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
        temp = await ctx.send('🔄 Loading playlist tracks...')
        
        with yt_dlp.YoutubeDL({'extract_flat': True, 'quiet': True, 'no_warnings': True}) as ydl:
            print(f"DEBUG: Extracting playlist from {search}")
            info = ydl.extract_info(search, download=False)
            
            if 'entries' not in info:
                await temp.edit(content='❌ No tracks found in this playlist.')
                return
            
            entries = info['entries']
            print(f"DEBUG: Found {len(entries)} entries in playlist")
            
            if not entries:
                await temp.edit(content='❌ Playlist is empty.')
                return
            
            tracks = []
            # Process entries with progress
            for idx, entry in enumerate(entries[:50]):  # Limit to 50 tracks
                try:
                    if isinstance(entry, dict) and 'id' in entry:
                        video_id = entry['id']
                    else:
                        video_id = entry  # Sometimes entry is just the ID string
                    
                    track = await get_track_from_url(f"https://www.youtube.com/watch?v={video_id}")
                    if track:
                        tracks.append(track)
                        if idx % 10 == 0:
                            await temp.edit(content=f'🔄 Loading playlist tracks... ({idx+1}/{min(len(entries), 50)})')
                except Exception as e:
                    print(f"DEBUG: Failed to load track {idx}: {str(e)}")
                    continue
            
            if not tracks:
                await temp.edit(content='❌ Failed to load any tracks from playlist.')
                return
            
            # Add tracks to queue
            count = 0
            for track in tracks:
                if not vc.is_playing() and count == 0:
                    await play_track(ctx, vc, track)
                else:
                    vc.queue.append(track)
                    if vc.loop_all:
                        config.LOOPQ.append(track)
                count += 1
            
            await temp.delete()
            await ctx.send(embed=eg.playlist_added(count))
            print(f"DEBUG: Successfully loaded {count} tracks from playlist")

    except Exception as e:
        print(f"ERROR in add_playlist: {str(e)}")
        try:
            await temp.edit(content=f'❌ Error loading playlist: {str(e)}')
        except:
            await ctx.reply(f"❌ Error loading playlist: {str(e)}")

async def add_song(ctx: commands.Context, vc, search: str, now: bool):
    """
    Adds a song to the queue or plays it
    """
    try:
        # Check if it's a URL or search query
        if "youtube.com" in search or "youtu.be" in search:
            print(f"DEBUG: Processing YouTube URL: {search}")
            track = await get_track_from_url(search)
        else:
            print(f"DEBUG: Processing search query: {search}")
            track = await get_track_from_search(search)
        
        if not track:
            await ctx.reply("❌ Could not find or load this video/song.")
            return

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
        print(f"ERROR in add_song: {str(e)}")
        await ctx.reply(f"❌ Error finding song: {str(e)}")

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
            print(f"DEBUG: Extracting info from URL: {url}")
            info = ydl.extract_info(url, download=False)
            
            audio_url = info.get('url', '')
            title = info.get('title', 'Unknown')
            duration = info.get('duration', 0)
            
            print(f"DEBUG: Extracted - Title: {title}, Duration: {duration}s, Has URL: {bool(audio_url)}")
            
            if not audio_url:
                print(f"ERROR: No audio URL found for {title}")
                return None
            
            return Track(
                title=title,
                author=info.get('uploader', 'Unknown'),
                url=audio_url,
                duration=duration,
                thumbnail=info.get('thumbnail', '')
            )
        except Exception as e:
            print(f"ERROR in get_track_from_url: {str(e)}")
            return None
