from collections import deque
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from src.common.track import Track

if TYPE_CHECKING:
    import discord
    from discord.ext.commands import Context


@dataclass
class PlayerState:
    queue: deque[Track] = field(default_factory=deque)
    track_loop: bool = False
    loop_all: bool = False
    current_track: Track | None = None
    current_index: int | None = None
    ctx: "Context | None" = None
    now_playing_message: "discord.Message | None" = None

    def set_context(self, ctx: "Context") -> None:
        self.ctx = ctx

    def get_current_track(self) -> Track | None:
        return self.current_track

    def set_current_track(self, track: Track | None) -> None:
        self.current_track = track

    def get_current_index(self) -> int | None:
        return self.current_index

    def set_current_index(self, index: int | None) -> None:
        self.current_index = index

    def append_to_queue(self, track: Track) -> None:
        self.queue.append(track)

    def update_current_queue_track(self, track: Track) -> None:
        if self.current_index is None:
            return
        if 0 <= self.current_index < len(self.queue):
            self.queue[self.current_index] = track

    def advance_to_next_track(self) -> Track | None:
        if not self.queue:
            self.current_index = None
            return None

        next_index = 0 if self.current_index is None else self.current_index + 1
        if next_index >= len(self.queue):
            if not self.loop_all:
                self.current_index = None
                return None
            next_index = 0

        self.current_index = next_index
        return self.queue[next_index]

    def remove_from_queue(self, index: int) -> Track:
        track = self.queue[index]
        del self.queue[index]

        if self.current_index is None:
            return track

        if index < self.current_index:
            self.current_index -= 1
        elif index == self.current_index:
            self.current_index = index - 1

        return track

    def clear_queue(self) -> None:
        self.queue.clear()
        self.current_index = None
        self.current_track = None

    def is_track_loop_enabled(self) -> bool:
        return self.track_loop

    def set_track_loop(self, enabled: bool) -> None:
        self.track_loop = enabled

    def is_queue_loop_enabled(self) -> bool:
        return self.loop_all

    def set_queue_loop(self, enabled: bool) -> None:
        self.loop_all = enabled

    def disable_loops(self) -> None:
        self.track_loop = False
        self.loop_all = False
