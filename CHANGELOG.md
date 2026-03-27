# Changelog

## 2026-03-27

### Changes
- Python: switch the main development baseline from `3.11.4` to `3.14.0`, and make `0.1c` the default branch for ongoing work.
- Dependencies: update [`requirements.txt`](/f:/Code/orpheus/requirements.txt) to reflect Python `>= 3.14` and align local setup with the new interpreter target.
- Development workflow: treat Python `3.11.x` as the previous `0.1b` baseline and move active testing and day-to-day development to Python `3.14.0`.

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
