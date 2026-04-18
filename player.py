"""Leonify Player Engine - Audio-Wiedergabe für video & audio files via ffpyplayer."""

import random
from enum import Enum
from typing import Optional, Callable

try:
    from ffpyplayer.player import MediaPlayer
    FFPY_AVAILABLE = True
except ImportError:
    FFPY_AVAILABLE = False


class RepeatMode(Enum):
    OFF = "off"
    ALL = "all"
    ONE = "one"


class PlayerEngine:
    """
    Audio-player der mit ffpyplayer sowohl audio- als auch video-files als audio-only abspielt.
    d.h. ein mp4 von youtube wird wie ein mp3 behandelt - es kommt nur sound raus.
    """

    def __init__(self):
        self.queue: list[dict] = []      # liste von song dicts
        self.original_queue: list[dict] = []  # für un-shuffle
        self.index: int = -1
        self.media: Optional[MediaPlayer] = None
        self.is_playing: bool = False
        self.shuffle: bool = False
        self.repeat: RepeatMode = RepeatMode.OFF

        # callbacks die die UI setzen kann
        self.on_song_change: Optional[Callable[[dict], None]] = None
        self.on_state_change: Optional[Callable[[bool], None]] = None
        self.on_finish: Optional[Callable[[], None]] = None

    # ---------- queue management ----------

    def set_queue(self, songs: list[dict], start_index: int = 0):
        self.original_queue = list(songs)
        self.queue = list(songs)
        if self.shuffle:
            self._shuffle_queue(preserve_current=False)
        self.index = max(0, min(start_index, len(self.queue) - 1)) if self.queue else -1
        self._play_current()

    def add_to_queue(self, song: dict):
        self.queue.append(song)
        self.original_queue.append(song)

    def clear(self):
        self._stop_media()
        self.queue = []
        self.original_queue = []
        self.index = -1

    # ---------- playback control ----------

    def play_pause(self):
        if not self.media:
            if self.queue and 0 <= self.index < len(self.queue):
                self._play_current()
            return
        if self.is_playing:
            self.media.set_pause(True)
            self.is_playing = False
        else:
            self.media.set_pause(False)
            self.is_playing = True
        self._emit_state()

    def play(self):
        if not self.media and self.queue:
            self._play_current()
        elif self.media and not self.is_playing:
            self.media.set_pause(False)
            self.is_playing = True
            self._emit_state()

    def pause(self):
        if self.media and self.is_playing:
            self.media.set_pause(True)
            self.is_playing = False
            self._emit_state()

    def next(self):
        if not self.queue:
            return
        if self.repeat == RepeatMode.ONE:
            self._play_current()
            return
        if self.index + 1 < len(self.queue):
            self.index += 1
        elif self.repeat == RepeatMode.ALL:
            self.index = 0
        else:
            self._stop_media()
            if self.on_finish:
                self.on_finish()
            return
        self._play_current()

    def previous(self):
        if not self.queue:
            return
        # wenn wir über 3 sekunden im song sind, zurück zum anfang
        pos = self.get_position()
        if pos > 3.0:
            self.seek(0)
            return
        if self.index > 0:
            self.index -= 1
        elif self.repeat == RepeatMode.ALL:
            self.index = len(self.queue) - 1
        else:
            self.seek(0)
            return
        self._play_current()

    def seek(self, seconds: float):
        if self.media:
            try:
                self.media.seek(seconds, relative=False, accurate=True)
            except Exception:
                pass

    def get_position(self) -> float:
        if not self.media:
            return 0.0
        try:
            pts = self.media.get_pts()
            return float(pts) if pts else 0.0
        except Exception:
            return 0.0

    def get_duration(self) -> float:
        if not self.media:
            return 0.0
        try:
            md = self.media.get_metadata() or {}
            return float(md.get("duration") or 0.0)
        except Exception:
            return 0.0

    def set_volume(self, vol: float):
        if self.media:
            try:
                self.media.set_volume(max(0.0, min(1.0, vol)))
            except Exception:
                pass

    # ---------- modes ----------

    def toggle_shuffle(self) -> bool:
        self.shuffle = not self.shuffle
        if self.shuffle:
            self._shuffle_queue(preserve_current=True)
        else:
            self._unshuffle_queue()
        return self.shuffle

    def cycle_repeat(self) -> RepeatMode:
        order = [RepeatMode.OFF, RepeatMode.ALL, RepeatMode.ONE]
        cur = order.index(self.repeat)
        self.repeat = order[(cur + 1) % len(order)]
        return self.repeat

    # ---------- internals ----------

    def _shuffle_queue(self, preserve_current: bool):
        if not self.queue:
            return
        current = self.queue[self.index] if preserve_current and 0 <= self.index < len(self.queue) else None
        shuffled = list(self.queue)
        random.shuffle(shuffled)
        if current:
            shuffled.remove(current)
            shuffled.insert(0, current)
            self.index = 0
        self.queue = shuffled

    def _unshuffle_queue(self):
        if not self.queue or not self.original_queue:
            return
        current = self.queue[self.index] if 0 <= self.index < len(self.queue) else None
        self.queue = list(self.original_queue)
        if current:
            try:
                self.index = self.queue.index(current)
            except ValueError:
                self.index = 0

    def _play_current(self):
        if not self.queue or not (0 <= self.index < len(self.queue)):
            return
        song = self.queue[self.index]
        file_path = song.get("file_path")
        if not file_path:
            return

        self._stop_media()

        if not FFPY_AVAILABLE:
            # dev-modus ohne ffpyplayer - nur event feuern
            self.is_playing = True
            self._emit_song()
            self._emit_state()
            return

        # audio-only: video disabled
        ff_opts = {"vn": True, "sn": True, "paused": False}
        try:
            self.media = MediaPlayer(file_path, ff_opts=ff_opts)
            self.is_playing = True
            self._emit_song()
            self._emit_state()
        except Exception as e:
            print(f"[Leonify] Playback-Fehler: {e}")
            self.media = None
            self.is_playing = False
            self._emit_state()

    def _stop_media(self):
        if self.media:
            try:
                self.media.close_player()
            except Exception:
                pass
            self.media = None
        self.is_playing = False

    def _emit_song(self):
        if self.on_song_change and 0 <= self.index < len(self.queue):
            self.on_song_change(self.queue[self.index])

    def _emit_state(self):
        if self.on_state_change:
            self.on_state_change(self.is_playing)

    def current_song(self) -> Optional[dict]:
        if 0 <= self.index < len(self.queue):
            return self.queue[self.index]
        return None

    def tick(self):
        """
        sollte periodisch (z.b. alle 500ms) aufgerufen werden.
        prüft ob song zu ende ist → nächster.
        """
        if not self.media or not self.is_playing:
            return
        try:
            frame, val = self.media.get_frame()
            if val == "eof":
                self.next()
        except Exception:
            pass
