import random
from config import PREVIOUS_TRACKS, LOOPQ
import wavelink


def add_to_previous_queue(track: wavelink.GenericTrack):
    PREVIOUS_TRACKS.append(track)
    if len(PREVIOUS_TRACKS) > 10:
        PREVIOUS_TRACKS.pop(0)


def get_from_previous_tracks(pos: int) -> wavelink.GenericTrack:
    try:
        return PREVIOUS_TRACKS.pop(pos)
    except IndexError:
        return None
