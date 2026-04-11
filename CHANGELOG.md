# Changelog

## 2026-04-11

### Changes
- Docker development workflow: bind-mount [`bot.py`](/f:/Code/orpheus/bot.py) and [`src/`](/f:/Code/orpheus/src) into `/app` through [`docker-compose.yml`](/f:/Code/orpheus/docker-compose.yml) so Python source changes can be picked up with a container restart instead of a rebuild.
- Docker image contents: replace the broad `COPY . .` runtime copy in [`Dockerfile`](/f:/Code/orpheus/Dockerfile) with targeted copies for `bot.py` and `src/`, while keeping the broad copy commented for reference.
- Ignore rules: add local Python virtual environment folders to [`.gitignore`](/f:/Code/orpheus/.gitignore) and [`.dockerignore`](/f:/Code/orpheus/.dockerignore).

### Fixes
- Guild playback state: store recently played tracks per Discord guild in [`src/utils/play_utils.py`](/f:/Code/orpheus/src/utils/play_utils.py) so playback history does not leak between servers.

### Removed
- Immediate playback: remove the `playnow` command and related queue-bypass logic.

### Notes
- Rebuild the image after `Dockerfile`, `requirements.txt`, or dependency changes.
- Restart the Compose service after Python-only source changes with `docker compose restart`.

## 2026-04-10

### Changes
- Kubernetes manifests: add [`k8s/namespace.yaml`](/f:/Code/orpheus/k8s/namespace.yaml) to define an `orpheus` namespace for isolating bot resources from the default cluster workspace.
- Deployment config: add and iterate on [`k8s/deployment.yaml`](/f:/Code/orpheus/k8s/deployment.yaml) to run the Discord bot as a single-replica Kubernetes `Deployment` backed by the existing `orpheus:latest` container image.
- Runtime env wiring: configure the Deployment to read `DISCORD_TOKEN`, `SPOTIFY_CLIENT_ID`, and `SPOTIFY_CLIENT_SECRET` from the `orpheus-secrets` Kubernetes `Secret`.
- Secret template: add [`k8s/secret.example.yaml`](/f:/Code/orpheus/k8s/secret.example.yaml) as a repository-safe example of the required Kubernetes `Secret` structure and keys.
- Log behavior: set `PYTHONUNBUFFERED=1` in the Deployment environment so bot startup and playback logs appear immediately through `kubectl logs`.

### Notes
- The current Kubernetes setup targets local learning and testing on a `kind` cluster rather than a production multi-node environment.
- The bot is intentionally configured with a single replica because the current Discord voice and in-memory playback state are not designed for multiple concurrent bot instances using the same token.
- Local Kubernetes secrets can be created directly from the existing `.env` file with `kubectl create secret generic orpheus-secrets --from-env-file=.env` before applying the Deployment.

## 2026-04-09

### Changes
- Containerization: add a root [`Dockerfile`](/f:/Code/orpheus/Dockerfile) for building the bot into a reusable Docker image with `python:3.14-slim`.
- Runtime setup: install `ffmpeg` in the Docker image so voice playback works without a separate host-level FFmpeg install.
- Compose workflow: add [`docker-compose.yml`](/f:/Code/orpheus/docker-compose.yml) to standardize local container startup, `.env` loading, restart behavior, and log-friendly Python output.
- Build context: add [`.dockerignore`](/f:/Code/orpheus/.dockerignore) so local cache files, Git metadata, and secrets are not copied into the Docker build context.
- Documentation: expand [`README.md`](/f:/Code/orpheus/README.md) with local and Docker run instructions, log commands, and environment variable setup guidance.

### Notes
- Docker logs are configured to be easier to follow by setting `PYTHONUNBUFFERED=1` in Compose.
- The current Docker runtime is defined separately from the local Python prerequisite notes in the project docs.

## 2026-04-03

### Changes
- Project structure: reorganize the codebase under `src/` and keep [`bot.py`](/f:/Code/orpheus/bot.py) as the external startup entrypoint.
- Module layout: move music playback and source helpers into [`src/utils/play_utils.py`](/f:/Code/orpheus/src/utils/play_utils.py), [`src/utils/ytb_utils.py`](/f:/Code/orpheus/src/utils/ytb_utils.py), and [`src/utils/spotify_utils.py`](/f:/Code/orpheus/src/utils/spotify_utils.py).
- Shared modules: keep the track model and embed helpers together in [`src/common/track.py`](/f:/Code/orpheus/src/common/track.py) and [`src/common/embeds.py`](/f:/Code/orpheus/src/common/embeds.py).
- Imports: standardize internal references so utility modules are imported by module name and functions are accessed through module-qualified calls.
- Packaging: remove `__init__.py` marker files under `src/` and rely on namespace-package behavior for the current project layout.

### Removed
- Legacy scripts: remove the obsolete [`scripts/youtube.py`](/f:/Code/orpheus/scripts/youtube.py) helper after the move to the current `yt-dlp` playback flow.
- Java runtime bundle: remove the unused `openjdk-19.0.1_windows-x64_bin` directory after dropping the old Lavalink-based setup.
- Cleanup: delete stale cache files and obsolete refactor leftovers from the old layout.

### Notes
- This update is primarily a refactor focused on simplifying the internal project structure rather than changing user-facing behavior.

## 2026-03-27

### Changes
- Python: switch the main development baseline from `3.11.4` to `3.14.0`, and make `0.1c` the default branch for ongoing work.
- Dependencies: update [`requirements.txt`](/f:/Code/orpheus/requirements.txt) to reflect Python `>= 3.14` and align local setup with the new interpreter target.
- Development workflow: treat Python `3.11.x` as the previous `0.1b` baseline and move active testing and day-to-day development to Python `3.14.0`.

### Fixes
- Startup lifecycle: move one-time bot initialization out of `on_ready()` and into `setup_hook()` to avoid duplicate startup work during reconnects.

### Notes
- Recreate the virtual environment after moving from `0.1b` to `0.1c`.
- Reinstall dependencies before running `python bot.py`.

## 2026-03-25

### Breaking
- Playback architecture: remove the Wavelink/Lavalink-based runtime design and migrate the bot to local playback using `discord.py` voice, `yt-dlp`, and `spotipy`.
- Setup flow: drop the requirement for a separate Lavalink node and move the project toward a local FFmpeg-based playback pipeline.
- Queue and player internals: replace Wavelink player and queue assumptions with local queue state built around `discord.VoiceClient`, Python `deque`, and a project-defined `Track` object.

### Changes
- Dependencies: upgrade `discord.py` to `>= 2.3.0`, keep `discord.py[voice]`, and adopt `yt-dlp`, `spotipy`, and `python-dotenv` as core dependencies.
- Configuration: centralize runtime credential loading in [`config.py`](/f:/Code/orpheus/config.py) and load `DISCORD_TOKEN`, `SPOTIFY_CLIENT_ID`, and `SPOTIFY_CLIENT_SECRET` from `.env`.
- Bot startup: update [`bot.py`](/f:/Code/orpheus/bot.py) to use async cog loading and configuration-driven token startup.
- Playback core: rework [`utils/play_utils.py`](/f:/Code/orpheus/utils/play_utils.py) around a local `Track` model, direct FFmpeg playback, queue progression, loop handling, and recently played state.
- YouTube support: rework [`utils/ytb_utils.py`](/f:/Code/orpheus/utils/ytb_utils.py) to use `yt-dlp` for searches, direct URL resolution, playlist loading, and extracted stream playback.
- Spotify support: rework [`utils/spotify_utils.py`](/f:/Code/orpheus/utils/spotify_utils.py) to resolve Spotify tracks, playlists, and albums through `spotipy` and map them into playable YouTube searches.
- Queue and embeds: update [`utils/embed_utils.py`](/f:/Code/orpheus/utils/embed_utils.py) and [`utils/queue_utils.py`](/f:/Code/orpheus/utils/queue_utils.py) to work with local queue state and `Track` objects instead of Wavelink types.
- Player commands: adapt [`cogs/player.py`](/f:/Code/orpheus/cogs/player.py) and [`cogs/loop_queue.py`](/f:/Code/orpheus/cogs/loop_queue.py) to the new playback and loop model.

### Fixes
- Credentials: fix token and Spotify credential sourcing by using a shared config layer instead of scattered direct environment access.
- Naming: correct the Spotify secret naming to `SPOTIFY_CLIENT_SECRET` and clean up helper naming around the current track state.
- Loop state: align queue-loop behavior around `loop_all` and centralized saved queue state with `config.LOOPQ`.
- Legacy assumptions: remove or bypass several Wavelink-era assumptions in queue handling, playback flow, and cog logic.

### Removed
- Dependencies: remove `wavelink`, `pytube`, and `youtube_dl` from the intended runtime stack.
- Runtime services: remove the need for Lavalink and the surrounding Java-based setup from the core playback path.
- Old integration paths: remove Wavelink-specific player, queue, and Spotify integration behavior from the updated design.

### Notes
- A local `.env` file is expected to define `DISCORD_TOKEN`, `SPOTIFY_CLIENT_ID`, and `SPOTIFY_CLIENT_SECRET`.
- FFmpeg must be installed and available on the system path for audio playback.
- Spotify URLs still play indirectly by resolving metadata to YouTube results rather than streaming from Spotify itself.
