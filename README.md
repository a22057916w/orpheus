## Overview
Orpheus is a Discord music bot built with `discord.py` voice, `yt-dlp`, and `spotipy`.

## Prerequisites
* Python 3.14 or higher
* [FFmpeg](https://ffmpeg.org/download.html) available on your system path
* Discord and Spotify API credentials in a local `.env` file
* Docker with Docker Compose support (optional)

## Environment Variables
Create a local `.env` file with:
* `DISCORD_TOKEN`
* `SPOTIFY_CLIENT_ID`
* `SPOTIFY_CLIENT_SECRET`

## Setup And Run
For local development:
1. Create and activate a virtual environment.
2. Install dependencies with `pip install -r requirements.txt`.
3. Start the bot with `python bot.py`.

For Docker:
1. Build and start the bot with `docker compose up --build`.
2. Run it in the background with `docker compose up -d --build`.
3. Follow logs with `docker compose logs -f`.
4. Stop the service with `docker compose down`.

The included Docker setup:
* uses `python:3.14-slim` as the base image
* installs `ffmpeg` inside the container
* loads credentials from `.env` through `docker-compose.yml`
* sets `PYTHONUNBUFFERED=1` so debug output appears immediately in container logs

## Notes
* Playback uses `discord.py` voice, `yt-dlp`, and `spotipy`.
* Lavalink, Java, and OpenJDK are no longer required for this project.
* `.env` is intentionally excluded from Docker build context through `.dockerignore`.


