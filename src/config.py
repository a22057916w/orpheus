import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(env_path, override=True)

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4.1-mini')
OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')

# yt-dlp knobs. YouTube keeps changing which player client hands out stream URLs that
# FFmpeg is actually allowed to fetch, so the client order is overridable without a
# code change. Comma separated; use "default" for yt-dlp's own client selection.
YTDLP_PLAYER_CLIENTS = os.getenv('YTDLP_PLAYER_CLIENTS', '')
# Optional cookies, needed for age-restricted or region-locked videos.
YTDLP_COOKIE_FILE = os.getenv('YTDLP_COOKIE_FILE')
YTDLP_COOKIES_FROM_BROWSER = os.getenv('YTDLP_COOKIES_FROM_BROWSER')

PREFIX = '!'
