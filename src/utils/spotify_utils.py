import spotipy
from spotipy import SpotifyException
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOauthError

from src import config
from src.common.track import Track

sp = spotipy.Spotify(
    auth_manager=SpotifyClientCredentials(
        client_id=config.SPOTIFY_CLIENT_ID,
        client_secret=config.SPOTIFY_CLIENT_SECRET,
        requests_session=False  # Disable retry for token requests.
    ),
    # Disable retry for Spotify API requests so 429 returns control immediately.
    requests_session=False,
)


async def get_tracks(search: str) -> list[Track]:
    if 'spotify.com/track/' in search:
        track_id = search.split('track/')[1].split('?')[0]
        return [get_track(track_id)]

    if 'spotify.com/playlist/' in search:
        playlist_id = search.split('playlist/')[1].split('?')[0]
        return get_playlist_tracks(playlist_id)

    if 'spotify.com/album/' in search:
        album_id = search.split('album/')[1].split('?')[0]
        return get_album_tracks(album_id)

    raise ValueError('Invalid Spotify URL')


def get_track(track_id: str) -> Track:
    try:
        track_info = sp.track(track_id)
    except SpotifyException as e:
        raise Exception(f'Unable to load Spotify track: {spotify_error_message(e)}') from e
    except SpotifyOauthError as e:
        raise Exception(f'Unable to authenticate with Spotify: {str(e)}') from e
    except Exception as e:
        raise Exception(f'Unable to load Spotify track: {str(e)}') from e

    return track_from_spotify(track_info)


def get_playlist_tracks(playlist_id: str) -> list[Track]:
    try:
        results = sp.playlist_tracks(playlist_id)
    except SpotifyException as e:
        raise Exception(f'Unable to load Spotify playlist: {spotify_error_message(e)}') from e
    except SpotifyOauthError as e:
        raise Exception(f'Unable to authenticate with Spotify: {str(e)}') from e
    except Exception as e:
        raise Exception(f'Unable to load Spotify playlist: {str(e)}') from e

    return [
        track_from_spotify(item['track'])
        for item in results['items']
        if item.get('track')
    ]


def get_album_tracks(album_id: str) -> list[Track]:
    try:
        results = sp.album_tracks(album_id)
    except SpotifyException as e:
        raise Exception(f'Unable to load Spotify album: {spotify_error_message(e)}') from e
    except SpotifyOauthError as e:
        raise Exception(f'Unable to authenticate with Spotify: {str(e)}') from e
    except Exception as e:
        raise Exception(f'Unable to load Spotify album: {str(e)}') from e

    return [track_from_spotify(track_info) for track_info in results['items']]


def spotify_error_message(error: SpotifyException) -> str:
    if error.http_status == 429:
        retry_after = error.headers.get('Retry-After')
        if retry_after:
            return f'Spotify rate limit reached. Try again after {retry_after} seconds.'
        return 'Spotify rate limit reached. Try again later.'

    return error.msg


def track_from_spotify(track_info: dict) -> Track:
    artists = ', '.join(artist['name'] for artist in track_info.get('artists', []))
    duration = track_info.get('duration_ms', 0) // 1000
    images = track_info.get('album', {}).get('images', [])
    thumbnail = images[0]['url'] if images else None
    
    return Track(
        title=track_info.get('name', 'Unknown'),
        author=artists or 'Unknown',
        url='',
        duration=duration,
        thumbnail=thumbnail,
    )
