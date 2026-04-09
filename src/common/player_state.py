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
    ctx: "Context | None" = None
    loop_queue_snapshot: list[Track] = field(default_factory=list)
    now_playing_message: "discord.Message | None" = None

    def set_context(self, ctx: "Context") -> None:
        self.ctx = ctx

    def get_current_track(self) -> Track | None:
        return self.current_track

    def set_current_track(self, track: Track | None) -> None:
        self.current_track = track

    def append_to_queue(self, track: Track) -> None:
        self.queue.append(track)

    def prepend_to_queue(self, track: Track) -> None:
        self.queue.appendleft(track)

    def pop_next_track(self) -> Track | None:
        return self.queue.popleft() if self.queue else None

    def clear_queue(self) -> None:
        self.queue.clear()

    def is_track_loop_enabled(self) -> bool:
        return self.track_loop

    def set_track_loop(self, enabled: bool) -> None:
        self.track_loop = enabled

    def is_queue_loop_enabled(self) -> bool:
        return self.loop_all

    def set_queue_loop(self, enabled: bool) -> None:
        self.loop_all = enabled

    def get_loop_queue_snapshot(self) -> list[Track]:
        return self.loop_queue_snapshot

    def set_loop_queue_snapshot(self, tracks: list[Track]) -> None:
        self.loop_queue_snapshot = tracks

    def append_to_loop_queue_snapshot(self, track: Track) -> None:
        self.loop_queue_snapshot.append(track)

    def restore_loop_queue_snapshot(self) -> None:
        self.queue = deque(self.loop_queue_snapshot)

    def disable_loops(self) -> None:
        self.track_loop = False
        self.loop_all = False
        self.loop_queue_snapshot = []
