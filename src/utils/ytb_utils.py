import yt_dlp

from src.common.track import Track

YDL_OPTS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'extract_flat': False,
}


async def get_tracks(search: str) -> list[Track]:
    if 'list=' in search:
        return await get_playlist_tracks(search)

    if 'youtube.com' in search or 'youtu.be' in search:
        track = await get_track_from_url(search)
    else:
        track = await get_track_from_search(search)

    return [track] if track else []


async def get_playlist_tracks(search: str) -> list[Track]:
    with yt_dlp.YoutubeDL({'extract_flat': True, 'quiet': True, 'no_warnings': True}) as ydl:
        print(f'DEBUG: Extracting playlist from {search}')
        info = ydl.extract_info(search, download=False)

    entries = info.get('entries', [])
    print(f'DEBUG: Found {len(entries)} entries in playlist')

    tracks = []
    for entry in entries[:50]:
        if not entry:
            continue

        video_id = entry.get('id', '')
        url = entry.get('url') or f'https://www.youtube.com/watch?v={video_id}'
        if video_id and not url.startswith('http'):
            url = f'https://www.youtube.com/watch?v={video_id}'

        tracks.append(Track(
            title=entry.get('title', 'Unknown'),
            author=entry.get('uploader', 'Unknown'),
            url=url,
            duration=entry.get('duration', 0) or 0,
            thumbnail=entry.get('thumbnail', ''),
        ))

    return tracks


async def resolve_track(track: Track) -> Track:
    if not track.url:
        return await get_track_from_search(track.search_query)

    if 'youtube.com' in track.url or 'youtu.be' in track.url:
        return await get_track_from_url(track.url)

    return track


async def get_track_from_search(query: str) -> Track:
    with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
        try:
            info = ydl.extract_info(f'ytsearch:{query}', download=False)
            if 'entries' in info and info['entries']:
                entry = info['entries'][0]
                video_url = entry.get('webpage_url', entry.get('url', ''))
                audio_info = ydl.extract_info(video_url, download=False)
                audio_url = audio_info.get('url', '')
                return Track(
                    title=entry.get('title', 'Unknown'),
                    author=entry.get('uploader', 'Unknown'),
                    url=audio_url,
                    duration=entry.get('duration', 0),
                    thumbnail=entry.get('thumbnail', ''),
                )
        except Exception as e:
            raise Exception(f'Failed to search: {str(e)}')


async def get_track_from_url(url: str) -> Track:
    with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
        try:
            print(f'DEBUG: Extracting info from URL: {url}')
            info = ydl.extract_info(url, download=False)

            audio_url = info.get('url', '')
            title = info.get('title', 'Unknown')
            duration = info.get('duration', 0)

            print(f'DEBUG: Extracted - Title: {title}, Duration: {duration}s, Has URL: {bool(audio_url)}')

            if not audio_url:
                print(f'ERROR: No audio URL found for {title}')
                return None

            return Track(
                title=title,
                author=info.get('uploader', 'Unknown'),
                url=audio_url,
                duration=duration,
                thumbnail=info.get('thumbnail', ''),
            )
        except Exception as e:
            print(f'ERROR in get_track_from_url: {str(e)}')
            return None
