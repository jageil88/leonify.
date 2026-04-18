"""Leonify Importer - lokale media files in die library aufnehmen."""

import os
import shutil
import time
import uuid
from typing import Optional

AUDIO_EXTS = {".mp3", ".m4a", ".aac", ".ogg", ".opus", ".wav", ".flac", ".wma"}
VIDEO_EXTS = {".mp4", ".mkv", ".webm", ".mov", ".avi", ".3gp", ".flv", ".ts"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def is_supported_media(path: str) -> bool:
    ext = os.path.splitext(path)[1].lower()
    return ext in AUDIO_EXTS or ext in VIDEO_EXTS


def is_image(path: str) -> bool:
    return os.path.splitext(path)[1].lower() in IMAGE_EXTS


def guess_title_from_filename(path: str) -> str:
    name = os.path.splitext(os.path.basename(path))[0]
    # ersetze underscores, trim
    return name.replace("_", " ").replace("-", " - ").strip()


def probe_duration(path: str) -> float:
    """versucht duration via ffpyplayer zu ermitteln. fallback = 0."""
    try:
        from ffpyplayer.player import MediaPlayer
        player = MediaPlayer(path, ff_opts={"vn": True, "sn": True, "paused": True})
        # kurz warten bis metadata geladen ist
        for _ in range(20):
            md = player.get_metadata() or {}
            dur = md.get("duration")
            if dur:
                player.close_player()
                return float(dur)
            time.sleep(0.05)
        player.close_player()
    except Exception:
        pass
    return 0.0


class Importer:
    def __init__(self, media_dir: str, covers_dir: str):
        self.media_dir = media_dir
        self.covers_dir = covers_dir
        os.makedirs(media_dir, exist_ok=True)
        os.makedirs(covers_dir, exist_ok=True)

    def _unique_name(self, directory: str, original: str) -> str:
        ext = os.path.splitext(original)[1].lower()
        return os.path.join(directory, f"{uuid.uuid4().hex}{ext}")

    def copy_media(self, src_path: str) -> Optional[str]:
        """kopiert das media-file in app-storage und returned den neuen path."""
        if not os.path.exists(src_path):
            return None
        if not is_supported_media(src_path):
            return None
        dest = self._unique_name(self.media_dir, src_path)
        try:
            shutil.copy2(src_path, dest)
            return dest
        except Exception as e:
            print(f"[Leonify] Import-fehler: {e}")
            return None

    def copy_cover(self, src_path: str) -> Optional[str]:
        if not os.path.exists(src_path) or not is_image(src_path):
            return None
        dest = self._unique_name(self.covers_dir, src_path)
        try:
            shutil.copy2(src_path, dest)
            return dest
        except Exception as e:
            print(f"[Leonify] Cover-fehler: {e}")
            return None

    def delete_file(self, path: str):
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass
