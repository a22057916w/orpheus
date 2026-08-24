## Overview
Orpheus is a Discord music bot built with `discord.py` voice, `yt-dlp`, and Spotify Web API calls.

## Prerequisites
* Python 3.14 or higher
* [FFmpeg](https://ffmpeg.org/download.html) available on your system path
* Discord and Spotify API credentials in a local `.env` file
* Docker with Docker Compose support (optional)
* `kubectl` if you want to deploy the bot to Kubernetes

## Environment Variables
Create a local `.env` file with:
* `DISCORD_TOKEN`
* `SPOTIFY_CLIENT_ID`
* `SPOTIFY_CLIENT_SECRET`
* `OPENAI_API_KEY` (optional, enables natural-language control when the bot is mentioned)
* `OPENAI_MODEL` and `OPENAI_BASE_URL` (optional, default to `gpt-4.1-mini` and the OpenAI API)

Optional yt-dlp overrides, useful when YouTube changes what it serves:
* `YTDLP_PLAYER_CLIENTS` - comma separated player clients to try in order, for example
  `android,default,ios`. Use `default` for yt-dlp's own client selection. Leave unset to use
  the built-in order.
* `YTDLP_COOKIE_FILE` - path to a Netscape-format cookies file, needed for age-restricted or
  region-locked videos.
* `YTDLP_COOKIES_FROM_BROWSER` - browser name to read cookies from instead, for example `chrome`.

## Setup And Run
For local development:
1. Create and activate a virtual environment.
2. Install dependencies with `pip install -r requirements.txt`.
3. Start the bot with `python bot.py`.

For Docker:
1. Build and start the bot in the foreground with `docker compose up --build`.
2. Build and start the bot in the background with `docker compose up -d --build`.
3. Follow logs with `docker compose logs -f`.
4. Stop the service with `docker compose down`.

For Docker updates:
* Rebuild after dependency or Dockerfile changes with `docker compose up --build`.
* Restart after Python source changes with `docker compose restart`.

The included Docker setup:
* uses `python:3.14-slim` as the base image
* installs `ffmpeg` inside the container
* loads credentials from `.env` through `docker-compose.yml`
* sets `PYTHONUNBUFFERED=1` so debug output appears immediately in container logs
* bind-mounts `bot.py` and `src/` into `/app` for faster local development

For Kubernetes with Docker Desktop:
1. Enable Kubernetes in Docker Desktop and wait for the cluster to become active.
2. Confirm your context is `docker-desktop` with `kubectl config current-context`.
3. Build the bot image with `docker build -t orpheus:latest .`.
4. Create the namespace with `kubectl apply -f k8s/namespace.yaml`.
5. Create the Kubernetes secret from the local `.env` file with `kubectl create secret generic orpheus-secrets --from-env-file=.env -n orpheus`.
6. Apply the Deployment with `kubectl apply -f k8s/deployment.yaml`.
7. Check resources with `kubectl get all -n orpheus`.
8. Follow bot logs with `kubectl logs -f -n orpheus deployment/orpheus-bot`.

To update the Kubernetes deployment after changing the bot code:
1. Rebuild the image with `docker build -t orpheus:latest .`.
2. Restart the Deployment with `kubectl rollout restart deployment/orpheus-bot -n orpheus`.
3. Follow the new pod logs with `kubectl logs -f -n orpheus deployment/orpheus-bot`.

The included Kubernetes setup:
* uses [`k8s/namespace.yaml`](/f:/Code/orpheus/k8s/namespace.yaml) to isolate bot resources in the `orpheus` namespace
* uses [`k8s/deployment.yaml`](/f:/Code/orpheus/k8s/deployment.yaml) to run a single bot replica from the `orpheus:latest` image
* reads `DISCORD_TOKEN`, `SPOTIFY_CLIENT_ID`, and `SPOTIFY_CLIENT_SECRET` from the `orpheus-secrets` Kubernetes Secret
* includes [`k8s/secret.example.yaml`](/f:/Code/orpheus/k8s/secret.example.yaml) as a safe template for the required Secret keys
* keeps Python logs unbuffered by setting `PYTHONUNBUFFERED=1`

## Troubleshooting
* **A song is announced and then immediately reports that the queue concluded.** YouTube
  handed out a stream URL that FFmpeg is not allowed to fetch, so FFmpeg exits within
  milliseconds of starting. The bot now checks each candidate stream URL before playing and
  falls through to the next player client, but if every client is refused, run
  `pip install -U yt-dlp` first, then try `YTDLP_PLAYER_CLIENTS` or supply cookies.
* **`Could not play <title>: YouTube would not hand out a playable audio stream`.** Same cause,
  reported up front. The message lists what each player client returned.

## Notes
* Playback uses `discord.py` voice, `yt-dlp`, and Spotify Web API calls.
* Lavalink, Java, and OpenJDK are no longer required for this project.
* `.env` is intentionally excluded from Docker build context through `.dockerignore`.
* Run only one copy of the bot at a time. Stop the Docker Compose container before starting the Kubernetes Deployment with the same Discord token.
