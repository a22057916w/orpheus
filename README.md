## Prerequisites
* Python 3.14 or higher
* [FFmpeg](https://ffmpeg.org/download.html) available on your system path
* Discord and Spotify API credentials in a local `.env` file

## Installing
1. Create and activate a virtual environment.
2. Install dependencies with `pip install -r requirements.txt`.
3. Create a `.env` file with:
   * `DISCORD_TOKEN`
   * `SPOTIFY_CLIENT_ID`
   * `SPOTIFY_CLIENT_SECRET`

## Running
Start the bot locally with:

`python bot.py`

## Notes
* Playback now uses `discord.py` voice, `yt-dlp`, and `spotipy`.
* Lavalink, Java, and OpenJDK are no longer required for this project.


