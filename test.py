import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
import time

client_id = '3309ad26a1394013879d2d284d6ee963'
client_secret = '5aaaae91f4264ed9871d4fd38a1ad8f6'

client_credentials_manager = SpotifyClientCredentials(client_id, client_secret)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
