import os

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET_ID = os.getenv("SPOTIFY_CLIENT_SECRET_ID")

PREFIX = '!'


NO_AUDIO_IS_PLAYING = "No music is currently playing! Use *?play* to start playing some!"
BOT_NOT_IN_VOICE_CHANNEL = "I wasn't present in any voice channel to begin with!"

INVALID_INPUT = "No results were found."


# Error messages
USER_NOT_IN_SAME_VOICE_CHANNEL = "You are not in the voice channel I am playing in!"
USER_NOT_IN_VOICE_CHANNEL = "Join a voice channel first in order to use this command!"
INVALID_INPUT = "No results were found."


# store the message id of the now playing message
MESSAGE_NOW_PLAYING = None
PREVIOUS_TRACKS = []

LOOPQ = None
