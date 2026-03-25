import random
from config import PREVIOUS_TRACKS, LOOPQ
from collections import deque
from typing import Optional
from utils.play_utils import Track


def add_to_previous_queue(track: Track):
    PREVIOUS_TRACKS.append(track)
    if len(PREVIOUS_TRACKS) > 10:
        PREVIOUS_TRACKS.pop(0)


def get_from_previous_tracks(pos: int) -> Optional[Track]:
    try:
        return PREVIOUS_TRACKS.pop(pos)
    except IndexError:
        return None


async def shuffle(queue: deque):
    temp = list(queue)
    queue.clear()
    random.shuffle(temp)
    queue.extend(temp)
