import base64
import time
from typing import Any

import requests

from src import config
from src.common.track import Track

SPOTIFY_ACCOUNTS_URL = 'https://accounts.spotify.com/api/token'
SPOTIFY_API_URL = 'https://api.spotify.com/v1'
MAX_PLAYLIST_TRACKS = 10

TOKEN: str | None = None
TOKEN_EXPIRES_AT = 0.0  # Spotify tokens usually expire after 3600 seconds.


def set_token() -> None:
    global TOKEN, TOKEN_EXPIRES_AT

    if not config.SPOTIFY_CLIENT_ID or not config.SPOTIFY_CLIENT_SECRET:
        raise Exception('Missing Spotify client credentials.')

    credentials = f'{config.SPOTIFY_CLIENT_ID}:{config.SPOTIFY_CLIENT_SECRET}'
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    # https://developer.spotify.com/documentation/web-api/tutorials/client-credentials-flow
    response = requests.post(
        SPOTIFY_ACCOUNTS_URL,
        data={'grant_type': 'client_credentials'},
        headers={'Authorization': f'Basic {encoded_credentials}'},
        timeout=10,
    )
    if response.status_code != 200:
        raise Exception(f'Spotify token API failed with {response.status_code}: {response.text}')

    token_info = response.json()
    TOKEN = token_info['access_token']
    # Refresh the token 60 seconds early to avoid using it right as it expires.
    TOKEN_EXPIRES_AT = time.time() + int(token_info.get('expires_in', 3600)) - 60


async def get_tracks(search: str) -> list[Track]:
    if not TOKEN or time.time() >= TOKEN_EXPIRES_AT:
        set_token()

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
        response = requests.get(
            f'{SPOTIFY_API_URL}/tracks/{track_id}',
            headers={'Authorization': f'Bearer {TOKEN}'},
            timeout=10,
        )

        if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 1))
                raise Exception(f'Spotify playlist API failed with 429. Retry after {retry_after} seconds: {response.text}')
        if response.status_code != 200:
            raise Exception(f'Spotify track API failed with {response.status_code}: {response.text}')  
        
        return track_from_spotify(response.json())
    except requests.RequestException as e:
        raise Exception(f'Unable to load Spotify track: {str(e)}') from e
    except Exception as e:
        raise Exception(f'Unable to load Spotify track: {str(e)}') from e


def get_playlist_tracks(playlist_id: str) -> list[Track]:
    """
    fields: Limits the Spotify response to only the data this bot uses.
    items: Playlist items returned by Spotify.
    track: The actual song inside each playlist item.
    name: Track title.
    type: Spotify item type, used to keep only tracks, exclude episodes or podcasts.
    duration_ms: Track duration in milliseconds.
    artists(name): Artist names for the track author.
    album(images): Album images for the track thumbnail.
    next: URL for the next page when a playlist has more than 100 items.
    limit: Number of playlist items to request per page.
    """

    tracks = []
    url = f'{SPOTIFY_API_URL}/playlists/{playlist_id}/items'
    params = {
        'fields': 'items(track(name,type,duration_ms,artists(name),album(images))),next',
        'limit': MAX_PLAYLIST_TRACKS,
    }

    try:
        # Fetch one playlist page at a time, up to 50 songs per request.
        while url:
            response = requests.get(
                url,
                headers={'Authorization': f'Bearer {TOKEN}'},
                params=params,
                timeout=10,
            )
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 1))
                raise Exception(f'Spotify playlist API failed with 429. Retry after {retry_after} seconds: {response.text}')

            if response.status_code != 200:
                raise Exception(f'Spotify playlist API failed with {response.status_code}: {response.text}')

            page = response.json()

            for item in page.get('items', []):
                track_info = item.get('track')
                if track_info and track_info.get('type') == 'track':
                    tracks.append(track_from_spotify(track_info))

            if len(tracks) >= MAX_PLAYLIST_TRACKS:
                break

            url = page.get('next')
            params = None

        return tracks
    except requests.RequestException as e:
        raise Exception(f'Unable to load Spotify playlist: {str(e)}') from e
    except Exception as e:
        raise Exception(f'Unable to load Spotify playlist: {str(e)}') from e


def get_album_tracks(album_id: str) -> list[Track]:
    try:
        response = requests.get(
            f'{SPOTIFY_API_URL}/albums/{album_id}',
            headers={'Authorization': f'Bearer {TOKEN}'},
            timeout=10,
        )
        if response.status_code != 200:
            raise Exception(f'Spotify album API failed with {response.status_code}: {response.text}')
        album_info = response.json()

        tracks = []
        page = album_info['tracks']
        while page:
            for track_info in page.get('items', []):
                tracks.append(track_from_spotify(
                    track_info,
                    default_images=album_info.get('images', []),
                ))

            next_url = page.get('next')
            if not next_url:
                break

            response = requests.get(
                next_url,
                headers={'Authorization': f'Bearer {TOKEN}'},
                timeout=10,
            )
            if response.status_code != 200:
                raise Exception(f'Spotify album tracks API failed with {response.status_code}: {response.text}')
            page = response.json()

        return tracks
    except requests.RequestException as e:
        raise Exception(f'Unable to load Spotify album: {str(e)}') from e
    except Exception as e:
        raise Exception(f'Unable to load Spotify album: {str(e)}') from e

def track_from_spotify(
    track_info: dict[str, Any],
    default_images: list[dict[str, Any]] | None = None,
) -> Track:
    artists = ', '.join(artist['name'] for artist in track_info.get('artists', []))
    duration = track_info.get('duration_ms', 0) // 1000
    images = track_info.get('album', {}).get('images', []) or default_images or []
    thumbnail = images[0]['url'] if images else None

    return Track(
        title=track_info.get('name', 'Unknown'),
        author=artists or 'Unknown',
        url='',
        duration=duration,
        thumbnail=thumbnail,
    )
