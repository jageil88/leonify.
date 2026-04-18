"""Leonify - offline music player app.

Hauptdatei: App, Screens, Navigation, Player-wiring.
"""

import os

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import StringProperty, NumericProperty, BooleanProperty, ObjectProperty
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.utils import platform

from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDIconButton, MDRaisedButton, MDFlatButton
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivymd.uix.list import OneLineAvatarIconListItem, IconLeftWidget, IconRightWidget
from kivymd.uix.textfield import MDTextField
from kivymd.uix.snackbar import Snackbar

import theme
from database import Database
from importer import Importer, is_supported_media, is_image, guess_title_from_filename, probe_duration
from player import PlayerEngine, RepeatMode


# ---------------------------------------------------------------------------
# KV-STRING - alle UI-layouts hier damit main.py ein drop-in file bleibt
# ---------------------------------------------------------------------------

KV = """
#:import theme theme

<RoundedCard@MDCard>:
    md_bg_color: theme.SURFACE_RGBA
    radius: [dp(14)]
    elevation: 0
    padding: dp(12)

<SongRow>:
    orientation: "horizontal"
    size_hint_y: None
    height: dp(64)
    padding: dp(8), dp(4)
    spacing: dp(12)

    MDCard:
        size_hint: None, None
        size: dp(48), dp(48)
        radius: [dp(8)]
        md_bg_color: theme.SURFACE_ALT_RGBA
        elevation: 0

        FitImage:
            source: root.cover_source
            radius: [dp(8)]

    BoxLayout:
        orientation: "vertical"
        padding: 0, dp(4)
        spacing: dp(2)

        MDLabel:
            text: root.title
            theme_text_color: "Custom"
            text_color: theme.TEXT_RGBA
            font_style: "Subtitle1"
            shorten: True
            shorten_from: "right"
            halign: "left"

        MDLabel:
            text: root.artist if root.artist else "unknown"
            theme_text_color: "Custom"
            text_color: theme.TEXT_MUTED_RGBA
            font_style: "Caption"
            shorten: True
            halign: "left"

    MDIconButton:
        icon: "heart" if root.is_favorite else "heart-outline"
        theme_icon_color: "Custom"
        icon_color: theme.SECONDARY_RGBA if root.is_favorite else theme.TEXT_MUTED_RGBA
        on_release: root.on_fav()

    MDIconButton:
        icon: "dots-vertical"
        theme_icon_color: "Custom"
        icon_color: theme.TEXT_MUTED_RGBA
        on_release: root.on_menu()


<LibraryScreen>:
    name: "library"

    MDBoxLayout:
        orientation: "vertical"
        md_bg_color: theme.BG_RGBA
        padding: 0, dp(12), 0, 0

        # Header
        MDBoxLayout:
            size_hint_y: None
            height: dp(48)
            padding: dp(16), 0
            spacing: dp(8)

            MDLabel:
                text: "Leonify"
                theme_text_color: "Custom"
                text_color: theme.PRIMARY_RGBA
                font_style: "H5"
                bold: True

            Widget:

            MDIconButton:
                icon: "magnify"
                theme_icon_color: "Custom"
                icon_color: theme.TEXT_RGBA
                on_release: root.toggle_search()

            MDIconButton:
                icon: "sort"
                theme_icon_color: "Custom"
                icon_color: theme.TEXT_RGBA
                on_release: root.cycle_sort()

        # Suchleiste (wird ein/ausgeblendet)
        MDBoxLayout:
            id: search_box
            size_hint_y: None
            height: 0
            opacity: 0
            padding: dp(16), 0

            MDTextField:
                id: search_field
                hint_text: "suche nach titel oder artist"
                mode: "rectangle"
                on_text: root.on_search_text(self.text)

        # Filter-chips
        MDBoxLayout:
            size_hint_y: None
            height: dp(40)
            padding: dp(16), 0
            spacing: dp(8)

            MDRaisedButton:
                id: filter_all
                text: "alle"
                md_bg_color: theme.PRIMARY_RGBA
                text_color: theme.TEXT_RGBA
                on_release: root.set_filter("all")

            MDRaisedButton:
                id: filter_fav
                text: "favoriten"
                md_bg_color: theme.SURFACE_ALT_RGBA
                text_color: theme.TEXT_RGBA
                on_release: root.set_filter("favorites")

            Widget:

        # Song-liste
        ScrollView:
            do_scroll_x: False
            MDBoxLayout:
                id: songs_container
                orientation: "vertical"
                adaptive_height: True
                padding: 0, dp(8), 0, dp(120)
                spacing: dp(2)


<PlaylistsScreen>:
    name: "playlists"

    MDBoxLayout:
        orientation: "vertical"
        md_bg_color: theme.BG_RGBA
        padding: 0, dp(12), 0, 0

        MDBoxLayout:
            size_hint_y: None
            height: dp(48)
            padding: dp(16), 0

            MDLabel:
                text: "Playlists"
                theme_text_color: "Custom"
                text_color: theme.TEXT_RGBA
                font_style: "H5"
                bold: True

            Widget:

            MDIconButton:
                icon: "plus"
                theme_icon_color: "Custom"
                icon_color: theme.PRIMARY_RGBA
                on_release: root.show_create_dialog()

        ScrollView:
            do_scroll_x: False
            MDBoxLayout:
                id: playlists_container
                orientation: "vertical"
                adaptive_height: True
                padding: dp(16), dp(8), dp(16), dp(120)
                spacing: dp(8)


<ImportScreen>:
    name: "import"

    MDBoxLayout:
        orientation: "vertical"
        md_bg_color: theme.BG_RGBA
        padding: dp(16), dp(16), dp(16), dp(16)
        spacing: dp(16)

        MDLabel:
            text: "Song importieren"
            theme_text_color: "Custom"
            text_color: theme.TEXT_RGBA
            font_style: "H5"
            bold: True
            size_hint_y: None
            height: self.texture_size[1]

        MDLabel:
            text: "pick ein video oder audio file - der ton wird als song gespeichert"
            theme_text_color: "Custom"
            text_color: theme.TEXT_MUTED_RGBA
            font_style: "Body2"
            size_hint_y: None
            height: self.texture_size[1]

        RoundedCard:
            size_hint_y: None
            height: dp(120)
            on_release: root.pick_media()

            BoxLayout:
                orientation: "vertical"
                spacing: dp(6)

                MDLabel:
                    text: root.picked_media_label
                    theme_text_color: "Custom"
                    text_color: theme.TEXT_RGBA
                    font_style: "Subtitle1"
                    halign: "center"

                MDLabel:
                    text: "tippen um file auszuwählen"
                    theme_text_color: "Custom"
                    text_color: theme.TEXT_MUTED_RGBA
                    font_style: "Caption"
                    halign: "center"

        MDTextField:
            id: title_field
            hint_text: "titel"
            mode: "rectangle"
            text: root.title_text
            on_text: root.title_text = self.text

        MDTextField:
            id: artist_field
            hint_text: "artist (optional)"
            mode: "rectangle"
            text: root.artist_text
            on_text: root.artist_text = self.text

        RoundedCard:
            size_hint_y: None
            height: dp(80)
            on_release: root.pick_cover()

            MDLabel:
                text: root.picked_cover_label
                theme_text_color: "Custom"
                text_color: theme.TEXT_RGBA
                font_style: "Subtitle1"
                halign: "center"

        Widget:

        MDRaisedButton:
            text: "song speichern"
            md_bg_color: theme.PRIMARY_RGBA
            text_color: theme.TEXT_RGBA
            size_hint: 1, None
            height: dp(48)
            on_release: root.save_song()


<PlayerScreen>:
    name: "player"

    MDBoxLayout:
        orientation: "vertical"
        md_bg_color: theme.BG_RGBA
        padding: dp(16)
        spacing: dp(16)

        MDBoxLayout:
            size_hint_y: None
            height: dp(48)

            MDIconButton:
                icon: "chevron-down"
                theme_icon_color: "Custom"
                icon_color: theme.TEXT_RGBA
                on_release: root.close_player()

            Widget:

            MDIconButton:
                icon: "pencil"
                theme_icon_color: "Custom"
                icon_color: theme.TEXT_MUTED_RGBA
                on_release: root.edit_current()

        Widget:
            size_hint_y: 0.05

        MDCard:
            id: cover_card
            size_hint: None, None
            size: dp(280), dp(280)
            pos_hint: {"center_x": 0.5}
            radius: [dp(20)]
            md_bg_color: theme.SURFACE_ALT_RGBA
            elevation: 0

            FitImage:
                id: cover_image
                source: root.cover_path
                radius: [dp(20)]

        Widget:
            size_hint_y: 0.05

        MDLabel:
            text: root.song_title
            theme_text_color: "Custom"
            text_color: theme.TEXT_RGBA
            font_style: "H6"
            halign: "center"
            size_hint_y: None
            height: self.texture_size[1]
            shorten: True

        MDLabel:
            text: root.song_artist if root.song_artist else "unknown"
            theme_text_color: "Custom"
            text_color: theme.TEXT_MUTED_RGBA
            font_style: "Body2"
            halign: "center"
            size_hint_y: None
            height: self.texture_size[1]

        # Fortschritt
        MDBoxLayout:
            orientation: "vertical"
            size_hint_y: None
            height: dp(36)

            MDSlider:
                id: seek_slider
                min: 0
                max: max(root.duration, 1)
                value: root.position
                hint: False
                color: theme.PRIMARY_RGBA
                on_touch_up: root.seek_from_slider(self)

            MDBoxLayout:
                size_hint_y: None
                height: dp(14)
                padding: dp(4), 0

                MDLabel:
                    text: root.format_time(root.position)
                    theme_text_color: "Custom"
                    text_color: theme.TEXT_MUTED_RGBA
                    font_style: "Caption"

                MDLabel:
                    text: root.format_time(root.duration)
                    theme_text_color: "Custom"
                    text_color: theme.TEXT_MUTED_RGBA
                    font_style: "Caption"
                    halign: "right"

        # Steuerung
        MDBoxLayout:
            size_hint_y: None
            height: dp(72)
            spacing: dp(8)
            padding: dp(8), 0

            MDIconButton:
                icon: "shuffle-variant" if root.shuffle_on else "shuffle-disabled"
                theme_icon_color: "Custom"
                icon_color: theme.PRIMARY_RGBA if root.shuffle_on else theme.TEXT_MUTED_RGBA
                on_release: root.toggle_shuffle()

            Widget:

            MDIconButton:
                icon: "skip-previous"
                theme_icon_color: "Custom"
                icon_color: theme.TEXT_RGBA
                user_font_size: "36sp"
                on_release: root.prev_song()

            MDIconButton:
                icon: "pause-circle" if root.is_playing else "play-circle"
                theme_icon_color: "Custom"
                icon_color: theme.PRIMARY_RGBA
                user_font_size: "72sp"
                on_release: root.play_pause()

            MDIconButton:
                icon: "skip-next"
                theme_icon_color: "Custom"
                icon_color: theme.TEXT_RGBA
                user_font_size: "36sp"
                on_release: root.next_song()

            Widget:

            MDIconButton:
                icon: root.repeat_icon
                theme_icon_color: "Custom"
                icon_color: theme.PRIMARY_RGBA if root.repeat_mode != "off" else theme.TEXT_MUTED_RGBA
                on_release: root.cycle_repeat()


<MiniPlayer>:
    size_hint_y: None
    height: dp(64)
    orientation: "horizontal"
    md_bg_color: theme.SURFACE_RGBA
    padding: dp(8)
    spacing: dp(12)

    MDCard:
        size_hint: None, None
        size: dp(48), dp(48)
        radius: [dp(8)]
        md_bg_color: theme.SURFACE_ALT_RGBA
        elevation: 0

        FitImage:
            source: root.cover_path
            radius: [dp(8)]

    BoxLayout:
        orientation: "vertical"
        padding: 0, dp(8)
        on_touch_up: root.open_full_player(*args)

        MDLabel:
            text: root.song_title
            theme_text_color: "Custom"
            text_color: theme.TEXT_RGBA
            font_style: "Subtitle2"
            shorten: True
            halign: "left"

        MDLabel:
            text: root.song_artist if root.song_artist else ""
            theme_text_color: "Custom"
            text_color: theme.TEXT_MUTED_RGBA
            font_style: "Caption"
            shorten: True
            halign: "left"

    MDIconButton:
        icon: "skip-previous"
        theme_icon_color: "Custom"
        icon_color: theme.TEXT_RGBA
        on_release: root.prev_song()

    MDIconButton:
        icon: "pause" if root.is_playing else "play"
        theme_icon_color: "Custom"
        icon_color: theme.PRIMARY_RGBA
        on_release: root.play_pause()

    MDIconButton:
        icon: "skip-next"
        theme_icon_color: "Custom"
        icon_color: theme.TEXT_RGBA
        on_release: root.next_song()


<BottomNav>:
    size_hint_y: None
    height: dp(60)
    orientation: "horizontal"
    md_bg_color: theme.SURFACE_RGBA
    padding: dp(8), 0

    MDIconButton:
        icon: "music-box-multiple"
        theme_icon_color: "Custom"
        icon_color: theme.PRIMARY_RGBA if root.active == "library" else theme.TEXT_MUTED_RGBA
        user_font_size: "28sp"
        size_hint_x: 1
        on_release: root.go("library")

    MDIconButton:
        icon: "playlist-music"
        theme_icon_color: "Custom"
        icon_color: theme.PRIMARY_RGBA if root.active == "playlists" else theme.TEXT_MUTED_RGBA
        user_font_size: "28sp"
        size_hint_x: 1
        on_release: root.go("playlists")

    MDIconButton:
        icon: "plus-circle"
        theme_icon_color: "Custom"
        icon_color: theme.SECONDARY_RGBA if root.active == "import" else theme.TEXT_MUTED_RGBA
        user_font_size: "28sp"
        size_hint_x: 1
        on_release: root.go("import")
"""


# ---------------------------------------------------------------------------
# WIDGETS
# ---------------------------------------------------------------------------


class SongRow(MDBoxLayout):
    """eine zeile in der song-liste."""
    song_id = NumericProperty(0)
    title = StringProperty("")
    artist = StringProperty("")
    cover_source = StringProperty("")
    is_favorite = BooleanProperty(False)

    on_tap_cb = ObjectProperty(None, allownone=True)
    on_fav_cb = ObjectProperty(None, allownone=True)
    on_menu_cb = ObjectProperty(None, allownone=True)

    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos):
            # nur wenn kein button getroffen wurde
            for child in self.children:
                if hasattr(child, "icon") and child.collide_point(*touch.pos):
                    return super().on_touch_up(touch)
            if self.on_tap_cb:
                self.on_tap_cb(self.song_id)
        return super().on_touch_up(touch)

    def on_fav(self):
        if self.on_fav_cb:
            self.on_fav_cb(self.song_id)

    def on_menu(self):
        if self.on_menu_cb:
            self.on_menu_cb(self.song_id)


class BottomNav(MDBoxLayout):
    active = StringProperty("library")

    def __init__(self, on_nav, **kwargs):
        super().__init__(**kwargs)
        self.on_nav = on_nav

    def go(self, screen_name: str):
        self.active = screen_name
        if self.on_nav:
            self.on_nav(screen_name)


class MiniPlayer(MDBoxLayout):
    song_title = StringProperty("nichts spielt gerade")
    song_artist = StringProperty("")
    cover_path = StringProperty("")
    is_playing = BooleanProperty(False)

    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app

    def play_pause(self):
        self.app.engine.play_pause()

    def next_song(self):
        self.app.engine.next()

    def prev_song(self):
        self.app.engine.previous()

    def open_full_player(self, instance, touch):
        if instance.collide_point(*touch.pos):
            self.app.open_player_screen()


# ---------------------------------------------------------------------------
# SCREENS
# ---------------------------------------------------------------------------


class LibraryScreen(Screen):
    current_filter = StringProperty("all")
    search_text = StringProperty("")
    sort_mode = StringProperty("added_desc")
    _search_visible = BooleanProperty(False)

    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app

    def on_pre_enter(self, *args):
        self.refresh()

    def refresh(self):
        container = self.ids.songs_container
        container.clear_widgets()

        if self.current_filter == "favorites":
            songs = self.app.db.list_favorites()
            if self.search_text:
                s = self.search_text.lower()
                songs = [x for x in songs if s in x["title"].lower() or s in (x.get("artist") or "").lower()]
        else:
            songs = self.app.db.list_songs(search=self.search_text, sort=self.sort_mode)

        if not songs:
            empty = MDLabel(
                text="noch keine songs\ntippe auf + unten um zu importieren",
                theme_text_color="Custom",
                text_color=theme.TEXT_MUTED_RGBA,
                halign="center",
                size_hint_y=None,
                height=dp(120)
            )
            container.add_widget(empty)
            return

        for s in songs:
            row = SongRow(
                song_id=s["id"],
                title=s["title"],
                artist=s.get("artist") or "",
                cover_source=s.get("cover_path") or "",
                is_favorite=bool(s.get("favorite")),
                on_tap_cb=lambda sid: self.play_song(sid, songs),
                on_fav_cb=self.toggle_fav,
                on_menu_cb=self.open_menu,
            )
            container.add_widget(row)

    def play_song(self, song_id: int, song_list: list):
        try:
            idx = next(i for i, s in enumerate(song_list) if s["id"] == song_id)
        except StopIteration:
            return
        self.app.engine.set_queue(song_list, start_index=idx)
        self.app.db.increment_plays(song_id)
        self.app.open_player_screen()

    def toggle_fav(self, song_id: int):
        self.app.db.toggle_favorite(song_id)
        self.refresh()

    def open_menu(self, song_id: int):
        self.app.show_song_menu(song_id, on_change=self.refresh)

    def toggle_search(self):
        self._search_visible = not self._search_visible
        box = self.ids.search_box
        if self._search_visible:
            box.height = dp(64)
            box.opacity = 1
        else:
            box.height = 0
            box.opacity = 0
            self.ids.search_field.text = ""
            self.search_text = ""
            self.refresh()

    def on_search_text(self, text: str):
        self.search_text = text
        self.refresh()

    def cycle_sort(self):
        order = ["added_desc", "title_asc", "artist_asc", "plays_desc"]
        idx = order.index(self.sort_mode) if self.sort_mode in order else 0
        self.sort_mode = order[(idx + 1) % len(order)]
        label = {
            "added_desc": "neueste zuerst",
            "title_asc": "titel a-z",
            "artist_asc": "artist a-z",
            "plays_desc": "meist gespielt",
        }[self.sort_mode]
        Snackbar(text=f"sortierung: {label}").open()
        self.refresh()

    def set_filter(self, f: str):
        self.current_filter = f
        self.ids.filter_all.md_bg_color = theme.PRIMARY_RGBA if f == "all" else theme.SURFACE_ALT_RGBA
        self.ids.filter_fav.md_bg_color = theme.PRIMARY_RGBA if f == "favorites" else theme.SURFACE_ALT_RGBA
        self.refresh()


class PlaylistsScreen(Screen):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app

    def on_pre_enter(self, *args):
        self.refresh()

    def refresh(self):
        container = self.ids.playlists_container
        container.clear_widgets()
        playlists = self.app.db.list_playlists()

        if not playlists:
            empty = MDLabel(
                text="keine playlists\ntipp + oben um eine zu erstellen",
                theme_text_color="Custom",
                text_color=theme.TEXT_MUTED_RGBA,
                halign="center",
                size_hint_y=None,
                height=dp(120)
            )
            container.add_widget(empty)
            return

        for p in playlists:
            card = MDCard(
                size_hint_y=None,
                height=dp(72),
                md_bg_color=theme.SURFACE_RGBA,
                radius=[dp(12)],
                elevation=0,
                padding=dp(16),
                ripple_behavior=True,
            )
            box = MDBoxLayout(orientation="horizontal", spacing=dp(12))
            icon = MDIconButton(
                icon="playlist-music",
                theme_icon_color="Custom",
                icon_color=theme.PRIMARY_RGBA,
            )
            texts = MDBoxLayout(orientation="vertical")
            texts.add_widget(MDLabel(
                text=p["name"],
                theme_text_color="Custom",
                text_color=theme.TEXT_RGBA,
                font_style="Subtitle1",
            ))
            texts.add_widget(MDLabel(
                text=f"{p['song_count']} songs",
                theme_text_color="Custom",
                text_color=theme.TEXT_MUTED_RGBA,
                font_style="Caption",
            ))
            delete_btn = MDIconButton(
                icon="delete-outline",
                theme_icon_color="Custom",
                icon_color=theme.TEXT_MUTED_RGBA,
            )
            delete_btn.bind(on_release=lambda _, pid=p["id"]: self.confirm_delete(pid))

            box.add_widget(icon)
            box.add_widget(texts)
            box.add_widget(delete_btn)
            card.add_widget(box)

            card.bind(on_release=lambda _, pid=p["id"]: self.open_playlist(pid))
            container.add_widget(card)

    def show_create_dialog(self):
        field = MDTextField(hint_text="playlist-name", mode="rectangle")

        def create(_):
            name = field.text.strip()
            if name:
                pid = self.app.db.create_playlist(name)
                dialog.dismiss()
                self.refresh()
                Snackbar(text=f"playlist '{name}' erstellt").open()

        dialog = MDDialog(
            title="neue playlist",
            type="custom",
            content_cls=field,
            buttons=[
                MDFlatButton(text="abbrechen", on_release=lambda _: dialog.dismiss()),
                MDRaisedButton(text="erstellen", md_bg_color=theme.PRIMARY_RGBA, on_release=create),
            ],
        )
        dialog.open()

    def confirm_delete(self, playlist_id: int):
        p = self.app.db.get_playlist(playlist_id)
        if not p:
            return

        def do_delete(_):
            self.app.db.delete_playlist(playlist_id)
            dialog.dismiss()
            self.refresh()

        dialog = MDDialog(
            title=f"playlist löschen?",
            text=f"'{p['name']}' wird entfernt (die songs bleiben in der library).",
            buttons=[
                MDFlatButton(text="nein", on_release=lambda _: dialog.dismiss()),
                MDRaisedButton(text="ja, löschen", md_bg_color=theme.DANGER_RGBA, on_release=do_delete),
            ],
        )
        dialog.open()

    def open_playlist(self, playlist_id: int):
        self.app.open_playlist_detail(playlist_id)


class ImportScreen(Screen):
    picked_media_path = StringProperty("")
    picked_cover_path = StringProperty("")
    picked_media_label = StringProperty("kein file ausgewählt")
    picked_cover_label = StringProperty("cover wählen (optional)")
    title_text = StringProperty("")
    artist_text = StringProperty("")

    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app

    def pick_media(self):
        self.app.pick_file(
            extensions_label="video/audio files",
            callback=self._on_media_picked,
            file_type="media",
        )

    def _on_media_picked(self, path: str):
        if not path or not is_supported_media(path):
            Snackbar(text="unsupported file").open()
            return
        self.picked_media_path = path
        fname = os.path.basename(path)
        self.picked_media_label = f"✓ {fname[:40]}"
        if not self.title_text:
            self.title_text = guess_title_from_filename(path)

    def pick_cover(self):
        self.app.pick_file(
            extensions_label="bilder",
            callback=self._on_cover_picked,
            file_type="image",
        )

    def _on_cover_picked(self, path: str):
        if not path or not is_image(path):
            Snackbar(text="bitte ein bild auswählen").open()
            return
        self.picked_cover_path = path
        fname = os.path.basename(path)
        self.picked_cover_label = f"✓ {fname[:30]}"

    def save_song(self):
        if not self.picked_media_path:
            Snackbar(text="erst video/audio file auswählen").open()
            return
        if not self.title_text.strip():
            Snackbar(text="titel darf nicht leer sein").open()
            return

        media_copy = self.app.importer.copy_media(self.picked_media_path)
        if not media_copy:
            Snackbar(text="import fehlgeschlagen").open()
            return
        cover_copy = ""
        if self.picked_cover_path:
            cover_copy = self.app.importer.copy_cover(self.picked_cover_path) or ""

        duration = probe_duration(media_copy)
        self.app.db.add_song(
            title=self.title_text.strip(),
            artist=self.artist_text.strip(),
            file_path=media_copy,
            cover_path=cover_copy,
            duration=duration,
        )

        Snackbar(text=f"'{self.title_text.strip()}' hinzugefügt ♥").open()

        # reset
        self.picked_media_path = ""
        self.picked_cover_path = ""
        self.picked_media_label = "kein file ausgewählt"
        self.picked_cover_label = "cover wählen (optional)"
        self.title_text = ""
        self.artist_text = ""

        # zurück zur library
        self.app.go_to("library")


class PlayerScreen(Screen):
    song_title = StringProperty("")
    song_artist = StringProperty("")
    cover_path = StringProperty("")
    is_playing = BooleanProperty(False)
    position = NumericProperty(0)
    duration = NumericProperty(0)
    shuffle_on = BooleanProperty(False)
    repeat_mode = StringProperty("off")
    repeat_icon = StringProperty("repeat-off")
    _seeking = BooleanProperty(False)

    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self._tick_event = None

    def on_enter(self, *args):
        self._refresh_from_engine()
        if not self._tick_event:
            self._tick_event = Clock.schedule_interval(self._tick, 0.5)

    def on_leave(self, *args):
        if self._tick_event:
            self._tick_event.cancel()
            self._tick_event = None

    def _refresh_from_engine(self):
        song = self.app.engine.current_song()
        if song:
            self.song_title = song.get("title", "")
            self.song_artist = song.get("artist") or ""
            self.cover_path = song.get("cover_path") or ""
        self.is_playing = self.app.engine.is_playing
        self.shuffle_on = self.app.engine.shuffle
        self.repeat_mode = self.app.engine.repeat.value
        self.repeat_icon = {
            "off": "repeat-off",
            "all": "repeat",
            "one": "repeat-once",
        }[self.repeat_mode]
        self.duration = self.app.engine.get_duration()

    def _tick(self, _dt):
        self.app.engine.tick()
        if not self._seeking:
            self.position = self.app.engine.get_position()
        if self.duration <= 0:
            self.duration = self.app.engine.get_duration()

    def play_pause(self):
        self.app.engine.play_pause()
        self.is_playing = self.app.engine.is_playing

    def next_song(self):
        self.app.engine.next()
        self._refresh_from_engine()

    def prev_song(self):
        self.app.engine.previous()
        self._refresh_from_engine()

    def toggle_shuffle(self):
        self.shuffle_on = self.app.engine.toggle_shuffle()

    def cycle_repeat(self):
        mode = self.app.engine.cycle_repeat()
        self.repeat_mode = mode.value
        self.repeat_icon = {
            RepeatMode.OFF: "repeat-off",
            RepeatMode.ALL: "repeat",
            RepeatMode.ONE: "repeat-once",
        }[mode]

    def seek_from_slider(self, slider):
        self._seeking = True
        target = float(slider.value)
        self.app.engine.seek(target)
        self.position = target
        Clock.schedule_once(lambda _: setattr(self, "_seeking", False), 0.3)

    def format_time(self, seconds: float) -> str:
        s = int(max(0, seconds))
        m, s = divmod(s, 60)
        return f"{m}:{s:02d}"

    def close_player(self):
        self.app.go_to("library")

    def edit_current(self):
        song = self.app.engine.current_song()
        if song:
            self.app.show_edit_dialog(song["id"])


# ---------------------------------------------------------------------------
# APP
# ---------------------------------------------------------------------------


class LeonifyApp(MDApp):

    def build(self):
        self.title = "Leonify"
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "DeepPurple"

        Builder.load_string(KV)

        Window.clearcolor = theme.BG_RGBA
        if platform != "android":
            Window.size = (400, 780)  # phone-proportionen für desktop-dev

        # storage paths
        storage = self._storage_path()
        self.db = Database(os.path.join(storage, "leonify.db"))
        self.importer = Importer(
            media_dir=os.path.join(storage, "media"),
            covers_dir=os.path.join(storage, "covers"),
        )

        # engine
        self.engine = PlayerEngine()
        self.engine.on_song_change = self._on_song_change
        self.engine.on_state_change = self._on_state_change

        # layout: screens + mini player + bottom nav
        root = MDBoxLayout(orientation="vertical", md_bg_color=theme.BG_RGBA)

        self.sm = ScreenManager(transition=NoTransition())
        self.library_screen = LibraryScreen(app=self)
        self.playlists_screen = PlaylistsScreen(app=self)
        self.import_screen = ImportScreen(app=self)
        self.player_screen = PlayerScreen(app=self)
        self.sm.add_widget(self.library_screen)
        self.sm.add_widget(self.playlists_screen)
        self.sm.add_widget(self.import_screen)
        self.sm.add_widget(self.player_screen)

        self.mini_player = MiniPlayer(app=self)
        self.mini_player.opacity = 0
        self.mini_player.size_hint_y = None
        self.mini_player.height = 0

        self.bottom_nav = BottomNav(on_nav=self.go_to)

        root.add_widget(self.sm)
        root.add_widget(self.mini_player)
        root.add_widget(self.bottom_nav)

        # android permissions
        if platform == "android":
            Clock.schedule_once(lambda _: self._request_android_perms(), 0.5)

        return root

    def _storage_path(self) -> str:
        if platform == "android":
            from android.storage import app_storage_path  # type: ignore
            return app_storage_path()
        return os.path.expanduser("~/.leonify")

    def _request_android_perms(self):
        try:
            from android.permissions import request_permissions, Permission  # type: ignore
            request_permissions([
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.READ_MEDIA_AUDIO,
                Permission.READ_MEDIA_VIDEO,
                Permission.READ_MEDIA_IMAGES,
            ])
        except Exception as e:
            print(f"[Leonify] permissions: {e}")

    # ---------- navigation ----------

    def go_to(self, name: str):
        self.sm.current = name
        self.bottom_nav.active = name
        # mini-player nur auf nicht-player screens zeigen
        if name == "player":
            self._hide_mini_player()
        elif self.engine.current_song():
            self._show_mini_player()

    def open_player_screen(self):
        self.go_to("player")

    def open_playlist_detail(self, playlist_id: int):
        # für v1: zeigt alle songs der playlist einfach als snackbar-liste / trigger playback
        songs = self.db.playlist_songs(playlist_id)
        if not songs:
            Snackbar(text="playlist ist leer - füg songs per menü hinzu").open()
            return
        self.engine.set_queue(songs, start_index=0)
        self.open_player_screen()

    # ---------- engine callbacks ----------

    def _on_song_change(self, song: dict):
        self.mini_player.song_title = song.get("title", "")
        self.mini_player.song_artist = song.get("artist") or ""
        self.mini_player.cover_path = song.get("cover_path") or ""
        if self.sm.current != "player":
            self._show_mini_player()

    def _on_state_change(self, is_playing: bool):
        self.mini_player.is_playing = is_playing

    def _show_mini_player(self):
        self.mini_player.height = dp(64)
        self.mini_player.opacity = 1

    def _hide_mini_player(self):
        self.mini_player.height = 0
        self.mini_player.opacity = 0

    # ---------- song menü (add to playlist / delete / edit) ----------

    def show_song_menu(self, song_id: int, on_change=None):
        song = self.db.get_song(song_id)
        if not song:
            return

        content = MDBoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(4))
        content.height = dp(180)

        dialog_ref = {}

        def close():
            if "d" in dialog_ref:
                dialog_ref["d"].dismiss()

        def edit(_):
            close()
            self.show_edit_dialog(song_id, on_change=on_change)

        def add_to_pl(_):
            close()
            self.show_add_to_playlist(song_id)

        def delete(_):
            close()
            self.confirm_delete_song(song_id, on_change=on_change)

        for text, icon, cb in [
            ("bearbeiten", "pencil", edit),
            ("zu playlist hinzufügen", "playlist-plus", add_to_pl),
            ("löschen", "delete", delete),
        ]:
            btn = MDFlatButton(
                text=text,
                size_hint_x=1,
                theme_text_color="Custom",
                text_color=theme.TEXT_RGBA,
                on_release=cb,
            )
            content.add_widget(btn)

        dialog = MDDialog(
            title=song["title"],
            type="custom",
            content_cls=content,
            buttons=[MDFlatButton(text="abbrechen", on_release=lambda _: close())],
        )
        dialog_ref["d"] = dialog
        dialog.open()

    def show_edit_dialog(self, song_id: int, on_change=None):
        song = self.db.get_song(song_id)
        if not song:
            return

        content = MDBoxLayout(orientation="vertical", spacing=dp(8), size_hint_y=None)
        content.height = dp(200)

        title_field = MDTextField(hint_text="titel", text=song["title"], mode="rectangle")
        artist_field = MDTextField(hint_text="artist", text=song.get("artist") or "", mode="rectangle")

        change_cover_btn = MDFlatButton(
            text="cover ändern",
            theme_text_color="Custom",
            text_color=theme.PRIMARY_RGBA,
        )

        new_cover_holder = {"path": ""}

        def pick(_):
            def on_cover(path):
                if path and is_image(path):
                    new_cover_holder["path"] = path
                    change_cover_btn.text = f"✓ {os.path.basename(path)[:20]}"
            self.pick_file(extensions_label="bilder", callback=on_cover, file_type="image")

        change_cover_btn.bind(on_release=pick)

        content.add_widget(title_field)
        content.add_widget(artist_field)
        content.add_widget(change_cover_btn)

        def save(_):
            cover_path = None
            if new_cover_holder["path"]:
                cover_path = self.importer.copy_cover(new_cover_holder["path"]) or None
            self.db.update_song(
                song_id,
                title=title_field.text.strip() or song["title"],
                artist=artist_field.text.strip(),
                cover_path=cover_path,
            )
            dialog.dismiss()
            Snackbar(text="gespeichert").open()
            if on_change:
                on_change()

        dialog = MDDialog(
            title="song bearbeiten",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(text="abbrechen", on_release=lambda _: dialog.dismiss()),
                MDRaisedButton(text="speichern", md_bg_color=theme.PRIMARY_RGBA, on_release=save),
            ],
        )
        dialog.open()

    def show_add_to_playlist(self, song_id: int):
        playlists = self.db.list_playlists()
        if not playlists:
            Snackbar(text="keine playlists - erstell erstmal eine").open()
            return

        content = MDBoxLayout(orientation="vertical", spacing=dp(4), size_hint_y=None)
        content.height = dp(min(60 * len(playlists) + 16, 400))

        dialog_ref = {}

        for p in playlists:
            def make_add(pid=p["id"], pname=p["name"]):
                def _add(_):
                    self.db.add_to_playlist(pid, song_id)
                    dialog_ref["d"].dismiss()
                    Snackbar(text=f"zu '{pname}' hinzugefügt").open()
                return _add

            btn = MDFlatButton(
                text=p["name"],
                size_hint_x=1,
                theme_text_color="Custom",
                text_color=theme.TEXT_RGBA,
                on_release=make_add(),
            )
            content.add_widget(btn)

        dialog = MDDialog(
            title="zu playlist hinzufügen",
            type="custom",
            content_cls=content,
            buttons=[MDFlatButton(text="abbrechen", on_release=lambda _: dialog.dismiss())],
        )
        dialog_ref["d"] = dialog
        dialog.open()

    def confirm_delete_song(self, song_id: int, on_change=None):
        song = self.db.get_song(song_id)
        if not song:
            return

        def do_delete(_):
            # file auch löschen
            self.importer.delete_file(song.get("file_path", ""))
            if song.get("cover_path"):
                self.importer.delete_file(song["cover_path"])
            self.db.delete_song(song_id)
            dialog.dismiss()
            Snackbar(text="gelöscht").open()
            if on_change:
                on_change()

        dialog = MDDialog(
            title="song löschen?",
            text=f"'{song['title']}' wird unwiderruflich entfernt.",
            buttons=[
                MDFlatButton(text="abbrechen", on_release=lambda _: dialog.dismiss()),
                MDRaisedButton(text="löschen", md_bg_color=theme.DANGER_RGBA, on_release=do_delete),
            ],
        )
        dialog.open()

    # ---------- file-picker ----------

    def pick_file(self, extensions_label: str, callback, file_type: str = "media"):
        """
        cross-platform file-picker.
        - android: plyer filechooser (native)
        - desktop: plyer filechooser fallback → kivy filechooser
        """
        if platform == "android":
            try:
                from plyer import filechooser  # type: ignore
                filters = []
                if file_type == "media":
                    filters = [("Media", "*.mp3", "*.m4a", "*.mp4", "*.mkv", "*.webm", "*.wav", "*.ogg", "*.opus", "*.flac", "*.aac")]
                elif file_type == "image":
                    filters = [("Images", "*.jpg", "*.jpeg", "*.png", "*.webp")]

                def _on_selection(selection):
                    if selection:
                        Clock.schedule_once(lambda _: callback(selection[0]), 0)

                filechooser.open_file(on_selection=_on_selection, filters=filters)
                return
            except Exception as e:
                print(f"[Leonify] plyer filechooser fehler: {e}")

        # desktop fallback
        try:
            from plyer import filechooser  # type: ignore

            def _on_selection(selection):
                if selection:
                    Clock.schedule_once(lambda _: callback(selection[0]), 0)

            filechooser.open_file(on_selection=_on_selection)
        except Exception as e:
            print(f"[Leonify] filechooser fehler: {e}")
            Snackbar(text="filechooser nicht verfügbar").open()


if __name__ == "__main__":
    LeonifyApp().run()
