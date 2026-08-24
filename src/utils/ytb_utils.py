import asyncio
import urllib.request

import yt_dlp

from src import config
from src.common.track import Track

# YouTube serves most adaptive (DASH) streams behind SABR / PO-token checks. The URLs those
# clients hand out extract fine but answer any outside fetch with 403, so FFmpeg exits
# immediately and playback looks like it "ended" the instant it started. Clients are tried
# in order and the first one whose stream URL actually responds wins. `None` means yt-dlp's
# own default client selection.
DEFAULT_PLAYER_CLIENTS = ('android', None, 'ios', 'web_safari', 'tv', 'mweb')

BASE_YDL_OPTS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'skip_download': True,
    'retries': 3,
    'socket_timeout': 15,
}

FLAT_YDL_OPTS = {
    'extract_flat': True,
    'quiet': True,
    'no_warnings': True,
    'skip_download': True,
    'socket_timeout': 15,
}

MAX_PLAYLIST_TRACKS = 50
STREAM_PROBE_TIMEOUT = 8
# yt-dlp errors are long and repetitive; keep the Discord reply readable.
MAX_FAILURE_REASON = 80


class TrackResolutionError(Exception):
    """Raised when no player client produced a stream that FFmpeg can open."""


def get_player_clients() -> tuple[str | None, ...]:
    configured = (config.YTDLP_PLAYER_CLIENTS or '').strip()
    if not configured:
        return DEFAULT_PLAYER_CLIENTS

    clients = []
    for name in configured.split(','):
        name = name.strip()
        if name:
            clients.append(None if name.lower() == 'default' else name)
    return tuple(clients) or DEFAULT_PLAYER_CLIENTS


def _apply_cookie_opts(opts: dict) -> None:
    if config.YTDLP_COOKIE_FILE:
        opts['cookiefile'] = config.YTDLP_COOKIE_FILE
    if config.YTDLP_COOKIES_FROM_BROWSER:
        opts['cookiesfrombrowser'] = (config.YTDLP_COOKIES_FROM_BROWSER,)


def _ydl_opts(client: str | None) -> dict:
    opts = dict(BASE_YDL_OPTS)
    if client:
        opts['extractor_args'] = {'youtube': {'player_client': [client]}}
    _apply_cookie_opts(opts)
    return opts


def _extract(target: str, opts: dict) -> dict | None:
    """Blocking yt-dlp extraction. Always call this through asyncio.to_thread."""
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(target, download=False)


def _first_entry(info: dict | None) -> dict | None:
    """Unwrap search results and playlists down to the first real video entry."""
    while info and info.get('entries') is not None:
        entries = [entry for entry in info.get('entries') or [] if entry]
        if not entries:
            return None
        info = entries[0]
    return info


def _stream_is_playable(url: str) -> bool:
    """Ask for the first byte exactly the way FFmpeg will, so a 403 is caught here instead
    of silently killing playback a few milliseconds after it starts. Deliberately sends no
    yt-dlp headers: FFmpeg does not send them either."""
    request = urllib.request.Request(url, headers={'Range': 'bytes=0-1'})
    try:
        with urllib.request.urlopen(request, timeout=STREAM_PROBE_TIMEOUT) as response:
            return response.status in (200, 206)
    except Exception as e:
        print(f'DEBUG: stream probe rejected the URL: {str(e)}')
        return False


def _short(error: Exception) -> str:
    reason = ' '.join(str(error).split()).removeprefix('ERROR: ')
    if len(reason) > MAX_FAILURE_REASON:
        reason = reason[:MAX_FAILURE_REASON].rstrip() + '...'
    return reason


def _track_from_info(info: dict) -> Track:
    return Track(
        title=info.get('title') or 'Unknown',
        author=info.get('uploader') or info.get('channel') or 'Unknown',
        url=info.get('webpage_url') or info.get('original_url') or '',
        duration=int(info.get('duration') or 0),
        thumbnail=info.get('thumbnail') or '',
        stream_url=info.get('url') or '',
    )


async def _resolve_playable(target: str) -> Track:
    """Extract `target` with each player client until one yields a usable stream URL."""
    failures = []

    for client in get_player_clients():
        label = client or 'default'
        try:
            info = await asyncio.to_thread(_extract, target, _ydl_opts(client))
        except Exception as e:
            print(f'DEBUG: extraction failed with player client {label}: {str(e)}')
            failures.append(f'{label}: {_short(e)}')
            continue

        entry = _first_entry(info)
        if not entry:
            failures.append(f'{label}: no results')
            continue

        stream_url = entry.get('url')
        if not stream_url:
            failures.append(f'{label}: no stream URL')
            continue

        if not await asyncio.to_thread(_stream_is_playable, stream_url):
            print(f'DEBUG: player client {label} returned a stream URL FFmpeg cannot fetch')
            failures.append(f'{label}: stream rejected (403)')
            continue

        print(f'DEBUG: resolved {entry.get("title")} via player client {label} '
              f'(format {entry.get("format_id")})')
        return _track_from_info(entry)

    raise TrackResolutionError(
        'YouTube would not hand out a playable audio stream. Tried ' + ', '.join(failures)
    )


async def get_tracks(search: str) -> list[Track]:
    if 'list=' in search:
        return await get_playlist_tracks(search)

    if 'youtube.com' in search or 'youtu.be' in search:
        target = search
    else:
        target = f'ytsearch1:{search}'

    return [await _resolve_playable(target)]


async def get_playlist_tracks(search: str) -> list[Track]:
    """Read a playlist without resolving streams; each track is resolved when it plays."""
    opts = dict(FLAT_YDL_OPTS)
    _apply_cookie_opts(opts)

    print(f'DEBUG: Extracting playlist from {search}')
    info = await asyncio.to_thread(_extract, search, opts)

    entries = (info or {}).get('entries') or []
    print(f'DEBUG: Found {len(entries)} entries in playlist')

    tracks = []
    for entry in entries[:MAX_PLAYLIST_TRACKS]:
        if not entry:
            continue

        video_id = entry.get('id', '')
        url = entry.get('webpage_url') or entry.get('url') or ''
        if video_id and not url.startswith('http'):
            url = f'https://www.youtube.com/watch?v={video_id}'

        tracks.append(Track(
            title=entry.get('title') or 'Unknown',
            author=entry.get('uploader') or entry.get('channel') or 'Unknown',
            url=url,
            duration=int(entry.get('duration') or 0),
            thumbnail=entry.get('thumbnail') or '',
        ))

    return tracks


async def resolve_track(track: Track) -> Track:
    """Return a Track carrying a stream URL that FFmpeg can open right now.

    Stream URLs expire, so a track that has been sitting in the queue is re-extracted from
    its page URL. One that was just resolved is kept, which saves a round trip on `!play`.
    """
    if track.stream_url and await asyncio.to_thread(_stream_is_playable, track.stream_url):
        return track

    target = track.url if track.url else f'ytsearch1:{track.search_query}'
    return await _resolve_playable(target)
