# Orpheus Discord Music Bot Update Plan

## Overview
This plan outlines the steps to update and revive the Orpheus Discord music bot. Based on the user's feedback, we will avoid using Wavelink and Lavalink if better alternatives exist. Instead, we'll use modern libraries like yt-dlp for YouTube, spotipy for Spotify, and discord.py's built-in voice support for audio playback. The bot will run locally on the user's machine, utilizing their existing Spotify API credentials and Discord server.

## Key Changes from Original Plan
- **Remove Wavelink/Lavalink**: Replace with yt-dlp (YouTube) and spotipy (Spotify) for better maintainability and performance.
- **Local Execution**: All components run locally; no need for external Lavalink server.
- **API Credentials**: User has Spotify credentials; we'll integrate them securely.
- **Modern Libraries**: Use yt-dlp instead of pytube/youtube_dl for YouTube handling.

## Prerequisites
- Python 3.10+
- FFmpeg installed locally (for audio processing)
- User's Spotify API credentials (Client ID and Secret)
- Discord bot token
- Access to user's Discord server for testing

## Phase 1: Environment and Dependencies Update (Foundation Fixes)
### 1.1 Update Dependencies
- Update `requirements.txt` to latest versions:
  - `discord.py >= 2.3.0` (for voice and latest API support)
  - `yt-dlp` (modern YouTube downloader, successor to youtube-dl)
  - `spotipy` (Spotify API wrapper)
  - `python-dotenv` (for secure environment variable loading)
  - Remove: `wavelink`, `pytube`, `youtube_dl` (deprecated)
- Install dependencies: `pip install -r requirements.txt`
- Ensure FFmpeg is installed (user can install via system package manager, e.g., `choco install ffmpeg` on Windows)

### 1.2 Secure API Credentials
- Create a `.env` file in the project root with:
  ```
  DISCORD_TOKEN=your_discord_bot_token
  SPOTIFY_CLIENT_ID=your_spotify_client_id
  SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
  ```
- Update `config.py` to load from `.env` using `python-dotenv`
- Remove hardcoded credentials from `bot.py`

### 1.3 Fix Discord Intents
- Ensure "Message Content Intent" is enabled in Discord Developer Portal
- Verify `intents.message_content = True` in `bot.py`

## Phase 2: Code Refactoring and Rewriting
### 2.1 Rewrite Core Playback Logic
- **Remove Wavelink**: Delete all Wavelink-related code from `bot.py`, `utils/play_utils.py`, `utils/ytb_utils.py`, `utils/spotify_utils.py`
- **New YouTube Handling** (`utils/ytb_utils.py`):
  - Use yt-dlp to search and stream YouTube audio
  - Support playlists and single tracks
  - Integrate with discord.py's `FFmpegPCMAudio` for playback
- **New Spotify Handling** (`utils/spotify_utils.py`):
  - Use spotipy to search Spotify tracks/playlists/albums
  - For each Spotify track, search equivalent on YouTube using yt-dlp (since Spotify doesn't allow direct streaming)
  - Handle playlists by iterating through tracks
- **Update Voice Management** (`utils/play_utils.py`):
  - Use discord.py's voice client directly
  - Implement queue management without Wavelink's Queue class
  - Add proper error handling for audio sources

### 2.2 Update Cogs
- **player.py**: Adapt commands to new playback system
- **loop_queue.py**: Update loop logic for new queue implementation
- **Remove/Archive Old Code**:
  - Delete `scripts/youtube.py` (obsolete)
  - Clean up `requirements.txt` comments

### 2.3 Add Logging and Error Handling
- Implement logging in `bot.py` and cogs (as noted in TO_DO.md)
- Add robust error handling for API failures, network issues, and invalid inputs

## Phase 3: Testing and Optimization
### 3.1 Local Testing
- Run bot locally: `python bot.py`
- Test basic commands: `!play` (YouTube/Spotify), `!pause`, `!skip`, etc.
- Verify queue functionality, loops, and voice channel management
- Test on user's Discord server

### 3.2 Cross-Platform Support
- Ensure compatibility with Windows (current) and Linux (as mentioned in TO_DO.md)
- Test FFmpeg integration across platforms

### 3.3 Performance Optimization
- Optimize audio buffering and streaming
- Handle large playlists efficiently
- Add rate limiting for API calls

## Phase 4: Deployment and Maintenance
### 4.1 Production Setup
- Set up as a background service on user's machine
- Monitor logs for issues
- Update dependencies periodically

### 4.2 Future Enhancements
- Add more music sources if needed
- Implement user preferences (e.g., volume control)
- Add web dashboard for queue management (optional)

## Risks and Contingencies
- **API Changes**: yt-dlp and spotipy may have breaking changes; monitor GitHub repos
- **Spotify Limitations**: Since we stream from YouTube, audio quality may vary; inform users
- **Local Resource Usage**: Audio processing may be CPU-intensive; monitor system resources
- **Fallback**: If new approach fails, revert to Wavelink as backup

## Timeline
- Phase 1: 1-2 days
- Phase 2: 3-5 days
- Phase 3: 1-2 days
- Phase 4: Ongoing

## Questions for User
- Confirm Spotify credentials are ready and valid
- Any specific features to prioritize (e.g., playlists over single tracks)?
- Preferred audio quality settings?
- Need help setting up FFmpeg or .env?</content>
<parameter name="filePath">f:\Code\orpheus\PLAN.md