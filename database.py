"""Leonify Datenbank - SQLite für Songs, Playlists, Favoriten."""

import os
import sqlite3
import time
from typing import Optional


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_dir()
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _ensure_dir(self):
        d = os.path.dirname(self.db_path)
        if d and not os.path.exists(d):
            os.makedirs(d, exist_ok=True)

    def _init_schema(self):
        c = self.conn.cursor()
        c.executescript("""
            CREATE TABLE IF NOT EXISTS songs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                artist TEXT DEFAULT '',
                file_path TEXT NOT NULL,
                cover_path TEXT DEFAULT '',
                duration REAL DEFAULT 0,
                favorite INTEGER DEFAULT 0,
                added_at INTEGER NOT NULL,
                play_count INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS playlists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                created_at INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS playlist_songs (
                playlist_id INTEGER NOT NULL,
                song_id INTEGER NOT NULL,
                position INTEGER NOT NULL,
                PRIMARY KEY (playlist_id, song_id),
                FOREIGN KEY (playlist_id) REFERENCES playlists(id) ON DELETE CASCADE,
                FOREIGN KEY (song_id) REFERENCES songs(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_songs_title ON songs(title);
            CREATE INDEX IF NOT EXISTS idx_songs_favorite ON songs(favorite);
            CREATE INDEX IF NOT EXISTS idx_playlist_songs_pos ON playlist_songs(playlist_id, position);
        """)
        self.conn.commit()

    # ---------- SONGS ----------

    def add_song(self, title: str, file_path: str, artist: str = "",
                 cover_path: str = "", duration: float = 0) -> int:
        c = self.conn.cursor()
        c.execute(
            "INSERT INTO songs (title, artist, file_path, cover_path, duration, added_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (title, artist, file_path, cover_path, duration, int(time.time()))
        )
        self.conn.commit()
        return c.lastrowid

    def update_song(self, song_id: int, title: Optional[str] = None,
                    artist: Optional[str] = None, cover_path: Optional[str] = None):
        updates = []
        values = []
        if title is not None:
            updates.append("title = ?")
            values.append(title)
        if artist is not None:
            updates.append("artist = ?")
            values.append(artist)
        if cover_path is not None:
            updates.append("cover_path = ?")
            values.append(cover_path)
        if not updates:
            return
        values.append(song_id)
        self.conn.execute(f"UPDATE songs SET {', '.join(updates)} WHERE id = ?", values)
        self.conn.commit()

    def delete_song(self, song_id: int):
        self.conn.execute("DELETE FROM songs WHERE id = ?", (song_id,))
        self.conn.commit()

    def get_song(self, song_id: int) -> Optional[dict]:
        row = self.conn.execute("SELECT * FROM songs WHERE id = ?", (song_id,)).fetchone()
        return dict(row) if row else None

    def list_songs(self, search: str = "", sort: str = "added_desc") -> list[dict]:
        order = {
            "added_desc": "added_at DESC",
            "added_asc": "added_at ASC",
            "title_asc": "LOWER(title) ASC",
            "title_desc": "LOWER(title) DESC",
            "artist_asc": "LOWER(artist) ASC, LOWER(title) ASC",
            "plays_desc": "play_count DESC, added_at DESC",
        }.get(sort, "added_at DESC")

        if search:
            pattern = f"%{search.lower()}%"
            rows = self.conn.execute(
                f"SELECT * FROM songs WHERE LOWER(title) LIKE ? OR LOWER(artist) LIKE ? "
                f"ORDER BY {order}",
                (pattern, pattern)
            ).fetchall()
        else:
            rows = self.conn.execute(f"SELECT * FROM songs ORDER BY {order}").fetchall()
        return [dict(r) for r in rows]

    def list_favorites(self) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM songs WHERE favorite = 1 ORDER BY added_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def toggle_favorite(self, song_id: int) -> bool:
        row = self.conn.execute("SELECT favorite FROM songs WHERE id = ?", (song_id,)).fetchone()
        if not row:
            return False
        new_val = 0 if row["favorite"] else 1
        self.conn.execute("UPDATE songs SET favorite = ? WHERE id = ?", (new_val, song_id))
        self.conn.commit()
        return bool(new_val)

    def increment_plays(self, song_id: int):
        self.conn.execute("UPDATE songs SET play_count = play_count + 1 WHERE id = ?", (song_id,))
        self.conn.commit()

    # ---------- PLAYLISTS ----------

    def create_playlist(self, name: str) -> int:
        c = self.conn.cursor()
        c.execute("INSERT INTO playlists (name, created_at) VALUES (?, ?)",
                  (name, int(time.time())))
        self.conn.commit()
        return c.lastrowid

    def rename_playlist(self, playlist_id: int, new_name: str):
        self.conn.execute("UPDATE playlists SET name = ? WHERE id = ?", (new_name, playlist_id))
        self.conn.commit()

    def delete_playlist(self, playlist_id: int):
        self.conn.execute("DELETE FROM playlists WHERE id = ?", (playlist_id,))
        self.conn.commit()

    def list_playlists(self) -> list[dict]:
        rows = self.conn.execute(
            "SELECT p.*, COUNT(ps.song_id) as song_count "
            "FROM playlists p LEFT JOIN playlist_songs ps ON p.id = ps.playlist_id "
            "GROUP BY p.id ORDER BY p.created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def get_playlist(self, playlist_id: int) -> Optional[dict]:
        row = self.conn.execute("SELECT * FROM playlists WHERE id = ?", (playlist_id,)).fetchone()
        return dict(row) if row else None

    def playlist_songs(self, playlist_id: int) -> list[dict]:
        rows = self.conn.execute(
            "SELECT s.*, ps.position FROM songs s "
            "JOIN playlist_songs ps ON s.id = ps.song_id "
            "WHERE ps.playlist_id = ? ORDER BY ps.position ASC",
            (playlist_id,)
        ).fetchall()
        return [dict(r) for r in rows]

    def add_to_playlist(self, playlist_id: int, song_id: int):
        row = self.conn.execute(
            "SELECT COALESCE(MAX(position), -1) + 1 as next_pos FROM playlist_songs WHERE playlist_id = ?",
            (playlist_id,)
        ).fetchone()
        next_pos = row["next_pos"]
        try:
            self.conn.execute(
                "INSERT INTO playlist_songs (playlist_id, song_id, position) VALUES (?, ?, ?)",
                (playlist_id, song_id, next_pos)
            )
            self.conn.commit()
        except sqlite3.IntegrityError:
            pass  # schon drin

    def remove_from_playlist(self, playlist_id: int, song_id: int):
        self.conn.execute(
            "DELETE FROM playlist_songs WHERE playlist_id = ? AND song_id = ?",
            (playlist_id, song_id)
        )
        self.conn.commit()

    def close(self):
        self.conn.close()
