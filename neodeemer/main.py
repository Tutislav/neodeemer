import json
import os
import sys
from functools import partial
from random import randint
from threading import Thread
from time import sleep

import certifi
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import DictProperty
from kivy.resources import resource_add_path, resource_find
from kivy.uix.image import AsyncImage
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.utils import platform
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.filemanager import MDFileManager
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.list import (IconLeftWidget, IconRightWidget, ILeftBody,
                             OneLineAvatarIconListItem,
                             TwoLineAvatarIconListItem, TwoLineIconListItem)
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.selection import MDSelectionList
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.tab import MDTabsBase
from plyer import notification

from download import Download
from localization import Localization
from songinfoloader import SpotifyLoader, YoutubeLoader
from tools import (TrackStates, check_update_available, font, open_url, submit_bugs,
                   check_mp3_available)
from webapi import WebApiServer

__version__ = "0.7"

class Loading(MDFloatLayout):
    pass

class MDSelectionListFix(MDSelectionList):
    def add_widget(self, widget, index=0, canvas=None):
        super().add_widget(widget, index, canvas)
        selection_icon = widget.parent.children[0]
        widget.parent.remove_widget(selection_icon)
        widget.parent.add_widget(selection_icon, 1)

class AsyncImageLeftWidget(ILeftBody, AsyncImage):
    pass

class ListLineArtist(TwoLineIconListItem):
    artist_dict = DictProperty()

    def __init__(self, *args, **kwargs):
        kwargs["text"] = font(kwargs["text"])
        kwargs["secondary_text"] = font(kwargs["secondary_text"])
        super().__init__(*args, **kwargs)

class ListLineAlbum(TwoLineIconListItem):
    album_dict = DictProperty()

    def __init__(self, *args, **kwargs):
        kwargs["text"] = font(kwargs["text"])
        kwargs["secondary_text"] = font(kwargs["secondary_text"])
        super().__init__(*args, **kwargs)

class ListLineTrack(TwoLineAvatarIconListItem):
    track_dict = DictProperty()

    def __init__(self, *args, **kwargs):
        kwargs["text"] = font(kwargs["text"])
        kwargs["secondary_text"] = font(kwargs["secondary_text"])
        super().__init__(*args, **kwargs)

class WindowManager(ScreenManager):
    pass

class SpotifyScreen(Screen):
    pass

class ArtistsTab(MDBoxLayout, MDTabsBase):
    tab_name = "ArtistsTab"

class AlbumsTab(MDBoxLayout, MDTabsBase):
    tab_name = "AlbumsTab"
    page = 1

class TracksTab(MDBoxLayout, MDTabsBase):
    tab_name = "TracksTab"
    page = 1

class YouTubeScreen(Screen):
    pass

class SPlaylistScreen(Screen):
    page = 1

class YPlaylistScreen(Screen):
    page = 1

class SettingsScreen(Screen):
    pass

class ErrorScreen(Screen):
    pass

class Neodeemer(MDApp):
    icon = "data/icon.png"
    loc = Localization()
    format_mp3 = False
    create_subfolders = True
    save_lyrics = True
    synchronized_lyrics = False
    webapi_enabled = False
    selected_tracks = []
    download_queue = []
    download_queue_info = {
        "position": 0,
        "downloaded_b": 0,
        "total_b": 0
    }
    playlist_queue = []
    unavailable_tracks = []
    intent_url = ""
    sound = None
    playlist_last = {
        "spotify": {},
        "youtube": {}
    }

    def build(self):
        self.theme_cls.primary_palette = "DeepPurple"
        self.theme_cls.accent_palette = "Amber"
        self.theme_cls.accent_hue = "700"
        self.theme_cls.accent_dark_hue = "900"
        LabelBase.register(name="Regular", fn_regular="fonts/MPLUS1p-Medium.ttf", fn_bold="fonts/MPLUS1p-ExtraBold.ttf")
        self.navigation_menu = self.root.ids.navigation_menu
        self.screen_manager = self.root.ids.screen_manager
        self.screens = [SpotifyScreen(name="SpotifyScreen")]
        self.screen_manager.add_widget(self.screens[0])
        Window.bind(on_keyboard=self.on_keyboard)
        self.screen_cur = self.screen_manager.current_screen
        self.toolbar = self.screen_cur.ids.toolbar
        self.progressbar = self.screen_cur.ids.progressbar
        self.artists_tab = self.screen_cur.ids.artists_tab
        self.albums_tab = self.screen_cur.ids.albums_tab
        self.tracks_tab = self.screen_cur.ids.tracks_tab
        self.file_manager = MDFileManager(exit_manager=self.file_manager_close, select_path=self.file_manager_select)
        if platform == "android":
            from android import activity, autoclass, mActivity
            from android.storage import primary_external_storage_path
            try:
                self.music_folder_path
            except:
                self.music_folder_path = os.path.join(primary_external_storage_path(), "Music")
            self.file_manager_default_path = primary_external_storage_path()
            self.download_threads_count = 2
            self.IntentClass = autoclass("android.content.Intent")
            self.intent = mActivity.getIntent()
            self.on_new_intent(self.intent)
            activity.bind(on_new_intent=self.on_new_intent)
        else:
            from kivy.config import Config
            Config.set("input", "mouse", "mouse,multitouch_on_demand")
            try:
                self.music_folder_path
            except:
                path = os.path.join(os.path.expanduser("~"), "Music")
                if not os.path.exists(path):
                    path = self.user_data_dir
                self.music_folder_path = path
            self.file_manager_default_path = os.path.expanduser("~")
            self.download_threads_count = 5
        Clock.schedule_once(self.after_start, 2)
        self.tab_switch(self.albums_tab)
        return
    
    def after_start(self, *args):
        self.tab_switch(self.tracks_tab)
        self.loading = MDDialog(type="custom", content_cls=Loading(), md_bg_color=(0, 0, 0, 0))
        self.label_loading_info = self.loading.children[0].children[2].children[0].ids.label_loading_info
        self.s = SpotifyLoader(self.loc.get_market(), self.music_folder_path, self.format_mp3, self.create_subfolders, self.label_loading_info, resource_find(".env"), resource_find("data/ytsfilter.json"), os.path.join(self.user_data_dir, ".cache"))
        self.y = YoutubeLoader(self.music_folder_path, self.format_mp3, self.create_subfolders, self.label_loading_info)
        self.watchdog = Thread()
        self.play_track = Thread()
        for i in range(1, self.download_threads_count + 1):
            globals()[f"download_tracks_{i}"] = Thread()
        self.webapi_watchdog = Thread()
        if self.webapi_enabled and not self.webapi_watchdog.is_alive():
            self.webapi_server = WebApiServer()
            self.webapi_watchdog = Thread(target=self.watchdog_webapi, name="webapi_watchdog")
            self.webapi_watchdog.start()
        self.navigation_menu_list = self.root.ids.navigation_menu_list
        if check_update_available(__version__):
            line = TwoLineIconListItem(text=self.loc.get("Update"), secondary_text=self.loc.get("New version is available"), on_press=lambda x:open_url("https://github.com/Tutislav/neodeemer/releases/latest", platform))
            self.navigation_menu_list.add_widget(line)
        self.submit_bug_dialog = MDDialog(
            title=self.loc.get("Submit bug"),
            text=self.loc.get("If some tracks has bad quality or even doesn't match the name you can submit it"),
            buttons=[
                MDFlatButton(text=self.loc.get("Submit bug"), on_press=lambda x:[submit_bugs(self.selected_tracks), self.submit_bug_dialog.dismiss()]),
                MDFlatButton(text=self.loc.get("Cancel"), on_press=lambda x:self.submit_bug_dialog.dismiss())
            ]
        )
        self.handle_intent(self.intent_url)
        self.intent_url = ""
    
    def on_stop(self):
        os.kill(os.getpid(), 9)

    def screen_switch(self, screen_name, direction="left"):
        if not self.screen_manager.has_screen(screen_name):
            Builder.load_file(screen_name.lower() + ".kv")
            screen = eval(screen_name + "()")
            screen.name = screen_name
            self.screens.append(screen)
            self.screen_manager.add_widget(screen)
            if "Playlist" in screen_name:
                if not hasattr(self, "playlist_last_menu"):
                    if screen_name == "SPlaylistScreen":
                        self.text_playlist_last = screen.ids.text_splaylist_id
                    else:
                        self.text_playlist_last = screen.ids.text_yplaylist_id
                    self.playlist_last_menu_list = []
                    self.playlist_last_menu = MDDropdownMenu(caller=self.text_playlist_last, items=self.playlist_last_menu_list, position="bottom", width_mult=20)
            elif screen_name == "SettingsScreen":
                if not hasattr(self, "localization_menu"):
                    self.switch_format = screen.ids.switch_format
                    self.switch_create_subfolders = screen.ids.switch_create_subfolders
                    self.text_music_folder_path = screen.ids.text_music_folder_path
                    self.switch_save_lyrics = screen.ids.switch_save_lyrics
                    self.options_lyrics = screen.ids.options_lyrics
                    self.switch_lyrics_type = screen.ids.switch_lyrics_type
                    self.switch_webapi_enabled = screen.ids.switch_webapi_enabled
                    self.text_localization = screen.ids.text_localization
                    self.localization_menu_list = [
                        {
                            "viewclass": "OneLineListItem",
                            "height": dp(50),
                            "text": f"{lang}",
                            "on_release": lambda x=lang:self.localization_menu_set(x)
                        } for lang in self.loc.LANGUAGES.keys()
                    ]
                    self.localization_menu = MDDropdownMenu(caller=self.text_localization, items=self.localization_menu_list, position="auto", width_mult=2)
            elif screen_name == "ErrorScreen":
                mdlist_tracks = screen.ids.mdlist_tracks
                mdlist_tracks.clear_widgets()
                for track in self.unavailable_tracks:
                    track_name = track["track_name"] + " - [b]" + track["artist_name"] + "[/b]"
                    secondary_text = self.loc.get(track["reason"])
                    line = ListLineTrack(text=track_name, secondary_text=secondary_text, track_dict=track)
                    line.add_widget(IconLeftWidget(icon="alert", on_press=lambda widget:self.mdlist_on_press(widget)))
                    mdlist_tracks.add_widget(line)
        self.screen_manager.direction = direction
        self.screen_manager.current = screen_name
        self.screen_cur = self.screen_manager.current_screen
        self.toolbar = self.screen_cur.ids.toolbar
        self.progressbar = self.screen_cur.ids.progressbar
        self.progressbar_update()
        if screen_name == "SettingsScreen":
            self.text_music_folder_path.text = self.music_folder_path
            self.text_localization.text = self.loc.get_lang()
    
    def tab_switch(self, tab_instance):
        tabs = self.screen_manager.current_screen.ids.tabs
        tabs.switch_tab(tab_instance.tab_label)
        self.tab_cur = tab_instance
    
    def on_tab_switch(self, instance_tabs, instance_tab, instance_tab_label, tab_text):
        self.tab_cur = instance_tab
    
    def on_new_intent(self, intent):
        action = intent.getAction()
        if action == self.IntentClass.ACTION_SEND:
            mime_type = intent.getType()
            if mime_type == "text/plain":
                text = intent.getStringExtra(self.IntentClass.EXTRA_TEXT)
                self.intent_url = text

    def handle_intent(self, intent_url="", *args):
        if intent_url != "":
            if "youtube.com" in intent_url or "youtu.be" in intent_url:
                if "playlist" in intent_url:
                    self.screen_switch("YPlaylistScreen")
                    self.text_playlist_last.text = intent_url
                    self.load_in_thread(self.playlist_load, self.tracks_actions_show, load_arg=True, show_arg=True, show_arg2=True)
                else:
                    tracks = self.y.tracks_search(intent_url)
                    if len(tracks) > 0:
                        self.download([tracks[0]])
            elif "spotify.com" in intent_url:
                intent_parts = intent_url.split("/")
                spotify_id = intent_parts[len(intent_parts) - 1]
                if "?" in spotify_id:
                    spotify_id = spotify_id.split("?")[0]
                if "/artist/" in intent_url:
                    artist = self.s.artist(spotify_id)
                    if artist != None:
                        self.tab_switch(self.albums_tab)
                        self.load_in_thread(self.albums_load, self.albums_show, artist)
                elif "/album/" in intent_url:
                    album = self.s.album(spotify_id)
                    if album != None:
                        self.tab_switch(self.tracks_tab)
                        self.load_in_thread(self.tracks_load, self.tracks_show, album)
                elif "/track/" in intent_url:
                    track = self.s.track(spotify_id)
                    if track != None:
                        self.download([track])
                elif "/playlist/" in intent_url:
                    self.screen_switch("SPlaylistScreen")
                    self.text_playlist_last.text = spotify_id
                    self.load_in_thread(self.playlist_load, self.tracks_actions_show, show_arg=True, show_arg2=True)
    
    def artists_load(self):
        text = self.artists_tab.ids.text_artists_search.text
        artists = self.s.artists_search(text)
        self.artists_tab.artists = artists
        if len(artists) > 0:
            return True
        else:
            Clock.schedule_once(partial(self.snackbar_show, self.loc.get("Error while loading artists")))
            return False
    
    def artists_show(self, *args):
        artists = self.artists_tab.artists
        mdlist_artists = self.artists_tab.ids.mdlist_artists
        mdlist_artists.clear_widgets()
        for artist in artists:
            if len(artist["artist_genres"]) > 0:
                genres = ""
                for i, genre in enumerate(artist["artist_genres"]):
                    genres += genre
                    if i < (len(artist["artist_genres"]) - 1):
                        genres += ", "
                secondary_text = genres
            else:
                secondary_text = " "
            line = ListLineArtist(text=artist["artist_name"], secondary_text=secondary_text, artist_dict=artist, on_press=lambda widget:self.load_in_thread(self.albums_load, self.albums_show, widget.artist_dict))
            line.add_widget(AsyncImageLeftWidget(source=artist["artist_image"]))
            mdlist_artists.add_widget(line)
    
    def albums_load(self, artist_dict=None, reset_page=True):
        if reset_page:
            self.albums_tab.page = 1
        if artist_dict != None:
            Clock.schedule_once(partial(self.text_widget_clear, self.albums_tab.ids.text_albums_search))
            albums = self.s.artist_albums(artist_dict, self.albums_tab.page)
        else:
            text = self.albums_tab.ids.text_albums_search.text
            albums = self.s.albums_search(text, self.albums_tab.page)
        self.albums_tab.albums = albums
        self.albums_tab.artist_dict = artist_dict
        if len(albums) > 0:
            return True
        else:
            Clock.schedule_once(partial(self.snackbar_show, self.loc.get("Error while loading albums")))
            return False
    
    def albums_show(self, *args):
        albums = self.albums_tab.albums
        artist_dict = self.albums_tab.artist_dict
        if artist_dict != None:
            self.tab_switch(self.albums_tab)
            self.albums_tab.title = "[b]" + artist_dict["artist_name"] + "[/b]"
        else:
            self.albums_tab.title = self.loc.get("[b]Albums[/b]")
        mdlist_albums = self.albums_tab.ids.mdlist_albums
        mdlist_albums.clear_widgets()
        for album in albums:
            if artist_dict != None:
                secondary_text = album["album_year"]
            else:
                secondary_text = "[b]" + album["artist_name"] + "[/b]  |  " + album["album_year"]
            line = ListLineAlbum(text=album["album_name"], secondary_text=secondary_text, album_dict=album, on_press=lambda widget:self.load_in_thread(self.tracks_load, self.tracks_show, widget.album_dict))
            line.add_widget(AsyncImageLeftWidget(source=album["album_image"]))
            mdlist_albums.add_widget(line)
        self.mdlist_add_page_controls(mdlist_albums)
    
    def tracks_load(self, album_dict=None, reset_page=True):
        if reset_page:
            self.tracks_tab.page = 1
        if album_dict != None:
            Clock.schedule_once(partial(self.text_widget_clear, self.tracks_tab.ids.text_tracks_search))
            tracks = self.s.album_tracks(album_dict)
        else:
            text = self.tracks_tab.ids.text_tracks_search.text
            tracks = self.s.tracks_search(text, self.tracks_tab.page)
        self.tracks_tab.tracks = tracks
        self.tracks_tab.album_dict = album_dict
        if len(tracks) > 0:
            return True
        else:
            Clock.schedule_once(partial(self.snackbar_show, self.loc.get("Error while loading tracks")))
            return False
    
    def tracks_show(self, *args):
        tracks = self.tracks_tab.tracks
        album_dict = self.tracks_tab.album_dict
        if album_dict != None:
            self.tab_switch(self.tracks_tab)
            self.tracks_tab.title = "[b]" + album_dict["album_name"] + "[/b]"
        else:
            self.tracks_tab.title = self.loc.get("[b]Tracks[/b]")
        mdlist_tracks = self.tracks_tab.ids.mdlist_tracks
        mdlist_tracks.clear_widgets()
        for track in tracks:
            if album_dict != None:
                track_name = str(track["track_number"]) + ".  " + track["track_name"]
                secondary_text = "      " + track["track_duration_str"]
            else:
                track_name = track["track_name"]
                secondary_text = track["track_duration_str"] + "  |  [b]" + track["artist_name"] + "[/b]  |  " + track["album_name"]
            line = ListLineTrack(text=track_name, secondary_text=secondary_text, track_dict=track)
            line.add_widget(IconLeftWidget(icon="play-circle-outline", on_press=lambda widget:self.play(widget)))
            if track["state"] == TrackStates.COMPLETED:
                line.add_widget(IconRightWidget(icon="check-circle"))
            else:
                line.add_widget(IconRightWidget(icon="download-outline", on_press=lambda widget:self.mdlist_on_press(widget)))
            mdlist_tracks.add_widget(line)
        if album_dict == None:
            self.mdlist_add_page_controls(mdlist_tracks)
    
    def youtube_load(self):
        text = self.screen_cur.ids.text_youtube_search.text
        tracks = self.y.tracks_search(text)
        self.screen_cur.tracks = tracks
        if len(tracks) > 0:
            return True
        else:
            Clock.schedule_once(partial(self.snackbar_show, self.loc.get("Error while loading tracks")))
            return False
    
    def playlist_load(self, youtube=False):
        if youtube:
            text = self.screen_cur.ids.text_yplaylist_id.text
            tracks = self.y.playlist_tracks(text)
            if len(self.playlist_last["youtube"]) > 3:
                del self.playlist_last["youtube"][list(self.playlist_last["youtube"].keys())[0]]
            if len(tracks) > 0:
                self.playlist_last["youtube"].update({tracks[0]["playlist_name"]: text})
        else:
            text = self.screen_cur.ids.text_splaylist_id.text
            tracks = self.s.playlist_tracks(text)
            if len(self.playlist_last["spotify"]) > 3:
                del self.playlist_last["spotify"][list(self.playlist_last["spotify"].keys())[0]]
            if len(tracks) > 0:
                self.playlist_last["spotify"].update({tracks[0]["playlist_name"]: text})
        self.screen_cur.tracks = tracks
        self.screen_cur.page = 1
        self.settings_save(False)
        if len(tracks) > 0:
            label_playlist_info = self.screen_cur.ids.label_playlist_info
            label_playlist_info.text = "[b]" + tracks[0]["playlist_name"] + "[/b] - [b]" + str(len(tracks)) + "[/b]" + self.loc.get_r(" songs")
            label_playlist_info.text = font(label_playlist_info.text)
            return True
        else:
            Clock.schedule_once(partial(self.snackbar_show, self.loc.get("Error while loading playlist")))
            return False
    
    def playlist_show(self, page=0, youtube=False, *args):
        tracks = self.screen_cur.tracks
        if page:
            limit, offset = self.s.limit_offset(page)
            tracks = tracks[offset:offset + limit]
        mdlist_tracks = self.screen_cur.ids.mdlist_tracks
        mdlist_tracks.clear_widgets()
        for track in tracks:
            if youtube:
                secondary_text = track["track_duration_str"] + "  |  [b]" + track["video_channel"] + "[/b]"
            else:
                secondary_text = track["track_duration_str"] + "  |  [b]" + track["artist_name"] + "[/b]  |  " + track["album_name"]
            line = ListLineTrack(text=track["track_name"], secondary_text=secondary_text, track_dict=track)
            line.add_widget(IconLeftWidget(icon="play-circle-outline", on_press=lambda widget:self.play(widget)))
            if track["state"] == TrackStates.COMPLETED:
                line.add_widget(IconRightWidget(icon="check-circle"))
            else:
                line.add_widget(IconRightWidget(icon="download-outline", on_press=lambda widget:self.mdlist_on_press(widget)))
            mdlist_tracks.add_widget(line)
        if page:
            self.mdlist_add_page_controls(mdlist_tracks)
    
    def load_in_thread(self, load_function, show_function=None, load_arg=None, load_arg2=None, show_arg=None, show_arg2=None):
        def load():
            if load_arg != None or load_arg2 != None:
                if load_arg2 != None:
                    show = load_function(load_arg, load_arg2)
                else:
                    show = load_function(load_arg)
            else:
                show = load_function()
            if show_function != None and show:
                if show_arg != None or show_arg2 != None:
                    if show_arg2 != None:
                        Clock.schedule_once(partial(show_function, show_arg, show_arg2))
                    else:
                        Clock.schedule_once(partial(show_function, show_arg))
                else:
                    Clock.schedule_once(show_function)
            Clock.schedule_once(self.loading.dismiss)
        self.loading.open()
        Thread(target=load, name="data_load").start()
    
    def download(self, selected_tracks=None):
        if selected_tracks != None:
            self.selected_tracks = selected_tracks
        for track in self.selected_tracks:
            if track["state"] != TrackStates.COMPLETED:
                self.download_queue.append(track)
            else:
                self.playlist_queue.append(track)
        self.selected_tracks = []
        if self.screen_cur.name != "SettingsScreen":
            if self.screen_cur.name == "SpotifyScreen":
                mdlist_tracks = self.tracks_tab.ids.mdlist_tracks
            else:
                mdlist_tracks = self.screen_cur.ids.mdlist_tracks
            self.mdlist_set_mode(mdlist_tracks, 0)
        for i in range(1, self.download_threads_count + 1):
            if not globals()[f"download_tracks_{i}"].is_alive():
                globals()[f"download_tracks_{i}"] = Thread(target=self.download_tracks_from_queue, name=f"download_tracks_{i}")
                globals()[f"download_tracks_{i}"].start()
        if not self.watchdog.is_alive():
            self.watchdog = Thread(target=self.watchdog_progress, name="watchdog")
            self.watchdog.start()
        self.snackbar_show(self.loc.get("Added to download queue"))
    
    def download_tracks_from_queue(self):
        while self.download_queue_info["position"] != len(self.download_queue):
            for track in self.download_queue:
                sleep(randint(0, self.download_threads_count * 4) / 100)
                if not track["locked"]:
                    track["locked"] = True
                    if any(state == track["state"] for state in [TrackStates.UNKNOWN, TrackStates.FOUND, TrackStates.SAVED]):
                        Download(track, self.s, self.download_queue_info, self.save_lyrics, self.synchronized_lyrics).download_track()
                    track["locked"] = False
                else:
                    continue
            sleep(1)
    
    def play(self, widget):
        if not self.play_track.is_alive():
            self.play_track = Thread(target=self.track_play, args=[widget], name="play_track")
            self.play_track.start()
    
    def track_play(self, widget, stream=True):
        Clock.schedule_once(self.loading.open)
        try:
            if widget.children[0].icon == "play-circle-outline":
                track_dict = widget.parent.parent.parent.children[0].track_dict
                track_dict_temp = {}
                track_dict_temp.update(track_dict)
                if self.sound != None:
                    self.sound.stop()
                    self.sound_prev_widget.children[0].icon = "play-circle-outline"
                if stream and track_dict_temp["state"] != TrackStates.COMPLETED:
                    try:
                        if track_dict_temp["state"] == TrackStates.UNKNOWN and track_dict_temp["video_id"] == None:
                            self.s.track_find_video_id(track_dict_temp)
                            track_dict["video_id"] = track_dict_temp["video_id"]
                            track_dict["state"] = track_dict_temp["state"]
                        if not check_mp3_available(track_dict):
                            raise
                        file_path = "https://neodeemer.vorpal.tk/mp3.php?video_id=" + track_dict_temp["video_id"] + ".mp3"
                        self.sound = SoundLoader.load(file_path)
                        self.sound.play()
                        widget.children[0].icon = "stop-circle"
                        self.sound_prev_widget = widget
                    except:
                        self.track_play(widget, False)
                        return
                elif track_dict_temp["state"] != TrackStates.COMPLETED:
                    track_dict_temp["forcedmp3"] = False
                    track_dict_temp["folder_path"] = self.user_data_dir
                    track_dict_temp["file_path"] = os.path.join(self.user_data_dir, "temp.m4a")
                    track_dict_temp["file_path2"] = os.path.join(self.user_data_dir, "temp.mp3")
                    if "playlist_name" in track_dict_temp:
                        del track_dict_temp["playlist_name"]
                    if track_dict_temp["state"] != TrackStates.COMPLETED:
                        if platform == "android":
                            if track_dict_temp["state"] == TrackStates.UNKNOWN and track_dict_temp["video_id"] == None:
                                self.s.track_find_video_id(track_dict_temp)
                            open_url("https://youtu.be/" + track_dict_temp["video_id"], platform)
                        else:
                            Download(track_dict_temp, self.s, None, False).download_track()
                        track_dict["video_id"] = track_dict_temp["video_id"]
                        track_dict["state"] = track_dict_temp["state"]
                if track_dict_temp["forcedmp3"]:
                    file_path = track_dict_temp["file_path2"]
                else:
                    file_path = track_dict_temp["file_path"]
                if track_dict_temp["state"] == TrackStates.COMPLETED:
                    self.sound = SoundLoader.load(file_path)
                    self.sound.play()
                    widget.children[0].icon = "stop-circle"
                    self.sound_prev_widget = widget
                elif track_dict_temp["state"] == TrackStates.UNAVAILABLE:
                    widget.children[0].icon = "alert"
                    Clock.schedule_once(partial(self.snackbar_show, self.loc.get("Error while playing track")))
            elif self.sound != None:
                self.sound.stop()
                widget.children[0].icon = "play-circle-outline"
        except:
            Clock.schedule_once(partial(self.snackbar_show, self.loc.get("Error while playing track")))
        Clock.schedule_once(self.loading.dismiss)
    
    def watchdog_progress(self):
        if len(self.unavailable_tracks) > 0:
            self.unavailable_tracks = []
            self.toolbar.left_action_items = []
        for track in self.playlist_queue:
            Download(track, self.s, self.download_queue_info, False).playlist_file_save()
        while self.download_queue_info["position"] != len(self.download_queue):
            Clock.schedule_once(self.progressbar_update)
            sleep(0.5)
        self.progressbar_update()
        for track in self.download_queue:
            if track["state"] == TrackStates.UNAVAILABLE:
                self.unavailable_tracks.append(track)
        tracks_count = len(self.download_queue) - len(self.unavailable_tracks)
        self.download_queue = []
        self.download_queue_info["position"] = 0
        self.download_queue_info["downloaded_b"] = 0
        self.download_queue_info["total_b"] = 0
        self.playlist_queue = []
        message = self.loc.get_r("Downloaded ") + str(tracks_count) + self.loc.get_r(" songs")
        if len(self.unavailable_tracks) > 0:
            message += "\n" + str(len(self.unavailable_tracks)) + self.loc.get_r(" songs can't be downloaded")
            Clock.schedule_once(partial(self.snackbar_show, str(len(self.unavailable_tracks)) + self.loc.get(" songs can't be downloaded")))
            left_action_items = [["alert", lambda x:self.screen_switch("ErrorScreen")]]
            self.toolbar.left_action_items = left_action_items
        if platform == "win":
            icon_path = resource_find("data/icon.ico")
        else:
            icon_path = resource_find("data/icon.png")
        notification.notify(title=self.loc.get_r("Download completed"), message=message, app_name=self.loc.TITLE_R, app_icon=icon_path)
    
    def watchdog_webapi(self):
        intent_url = ""
        while self.webapi_enabled or self.webapi_server.server_thread.is_alive():
            if self.webapi_server.intent_url != "":
                intent_url = self.webapi_server.intent_url
                self.webapi_server.intent_url = ""
            if intent_url != "":
                Clock.schedule_once(partial(self.handle_intent, intent_url))
                intent_url = ""
            sleep(0.5)

    def progressbar_update(self, *args):
        if self.download_queue_info["total_b"] > 0:
            if len(self.download_queue) <= 10:
                self.progressbar.value = int((self.download_queue_info["downloaded_b"] / self.download_queue_info["total_b"]) * 100)
            else:
                self.progressbar.value = int(self.download_queue_info["position"] / len(self.download_queue) * 100)
            self.toolbar.title = self.loc.TITLE + " - " + str(self.download_queue_info["position"]) + "/" + str(len(self.download_queue))
        elif len(self.download_queue) > 0:
            if self.toolbar.title == self.loc.TITLE or len(self.toolbar.title) >= (len(self.loc.TITLE) + 6):
                self.toolbar.title = self.loc.TITLE + " - "
            else:
                self.toolbar.title += "."
        else:
            self.progressbar.value = 0
            self.toolbar.title = self.loc.TITLE
    
    def snackbar_show(self, text, *args):
        Snackbar(text=text).open()
    
    def text_widget_clear(self, text_widget, *args):
        text_widget.text = ""

    def mdlist_on_press(self, widget):
        widget.parent.parent.parent.do_selected_item()
    
    def mdlist_selected(self, instance_selection_list, instance_selection_item):
        self.toolbar.title = str(len(instance_selection_list.get_selected_list_items()))
        line = instance_selection_item.children[0]
        if hasattr(line, "track_dict"):
            if not line.track_dict in self.selected_tracks:
                self.selected_tracks.append(line.track_dict)
        else:
            instance_selection_item.do_unselected_item()
            if not instance_selection_list.get_selected_list_items():
                Clock.schedule_once(partial(self.mdlist_set_mode, instance_selection_list, 0))
    
    def mdlist_unselected(self, instance_selection_list, instance_selection_item):
        if instance_selection_list.get_selected_list_items():
            self.toolbar.title = str(len(instance_selection_list.get_selected_list_items()))
        else:
            self.toolbar.title = self.loc.TITLE
        line = instance_selection_item.children[0]
        if hasattr(line, "track_dict"):
            if line.track_dict in self.selected_tracks:
                self.selected_tracks.remove(line.track_dict)
    
    def mdlist_set_mode(self, instance_selection_list, mode, *args):
        if mode:
            bg_color = self.theme_cls.accent_color
            left_action_items = [
                ["close", lambda x:self.mdlist_set_mode(instance_selection_list, 0)],
                ["bug-outline", lambda x:self.submit_bug_dialog.open()]
            ]
            if self.screen_cur.name != "ErrorScreen":
                self.tracks_actions_show()
        else:
            bg_color = self.theme_cls.primary_color
            left_action_items = []
            instance_selection_list.unselected_all()
            if self.screen_cur.name != "ErrorScreen":
                self.tracks_actions_show(False)
        Animation(md_bg_color=bg_color, d=0.2).start(self.toolbar)
        self.toolbar.left_action_items = left_action_items
    
    def mdlist_add_page_controls(self, mdlist):
        if self.screen_cur.name == "SpotifyScreen":
            view_cur = self.tab_cur
        else:
            view_cur = self.screen_cur
        line = OneLineAvatarIconListItem()
        if view_cur.page > 1:
            line.add_widget(IconLeftWidget(icon="arrow-left-bold", on_press=lambda x:self.tracks_change_page(False)))
        if view_cur.page < 10:
            line.add_widget(IconRightWidget(icon="arrow-right-bold", on_press=lambda x:self.tracks_change_page()))
        mdlist.add_widget(line)
    
    def tracks_change_page(self, next=True):
        if self.screen_cur.name == "SpotifyScreen":
            view_cur = self.tab_cur
        else:
            view_cur = self.screen_cur
        page_prev = view_cur.page
        if next and view_cur.page < 10:
            view_cur.page += 1
        elif not next and view_cur.page > 1:
            view_cur.page -= 1
        if view_cur.page != page_prev:
            view_cur.ids.scrollview.scroll_y = 1
            if self.screen_cur.name == "SpotifyScreen":
                if view_cur.tab_name == "TracksTab":
                    self.load_in_thread(self.tracks_load, self.tracks_show, load_arg2=False)
                elif view_cur.tab_name == "AlbumsTab":
                    text = self.albums_tab.ids.text_albums_search.text
                    mdlist_albums = self.albums_tab.ids.mdlist_albums
                    if len(mdlist_albums.children) > 1 and len(text) == 0:
                        album_dict = mdlist_albums.children[1].album_dict
                    else:
                        album_dict = None
                    self.load_in_thread(self.albums_load, self.albums_show, album_dict, False)
            elif self.screen_cur.name == "SPlaylistScreen":
                self.playlist_show(self.screen_cur.page, False)
            elif self.screen_cur.name == "YPlaylistScreen":
                self.playlist_show(self.screen_cur.page, True)

    def tracks_actions(self, action, youtube=False):
        if action == "download_all":
            if self.screen_cur.name == "SpotifyScreen":
                self.download(self.tracks_tab.tracks)
            else:
                self.download(self.screen_cur.tracks)
        elif action == "download_selected":
            self.download()
        elif action == "show":
            self.playlist_show(self.screen_cur.page, youtube)
    
    def tracks_actions_show(self, show=True, playlist=False, *args):
        if playlist:
            tracks_actions = self.screen_cur.ids.playlist_actions
        else:
            if self.screen_cur.name == "SpotifyScreen":
                tracks_actions = self.tracks_tab.ids.tracks_actions
            else:
                tracks_actions = self.screen_cur.ids.tracks_actions
        if show:
            tracks_actions.opacity = 1
            tracks_actions.height = 40
            tracks_actions.pos_hint = {"center_x": .5}
        else:
            tracks_actions.opacity = 0
            tracks_actions.height = 0
            tracks_actions.pos_hint = {"center_x": -1}
    
    def playlist_last_menu_show(self, youtube=False):
        if youtube:
            playlist_last_dict = self.playlist_last["youtube"]
            self.text_playlist_last = self.screen_cur.ids.text_yplaylist_id
        else:
            playlist_last_dict = self.playlist_last["spotify"]
            self.text_playlist_last = self.screen_cur.ids.text_splaylist_id
        self.playlist_last_menu_list = [
            {
                "viewclass": "OneLineListItem",
                "height": dp(50),
                "text": f"{playlist_id}",
                "on_release": lambda x=playlist_id:self.playlist_last_menu_set(playlist_last_dict[x], youtube)
            } for playlist_id in playlist_last_dict.keys()
        ]
        self.playlist_last_menu.caller = self.text_playlist_last
        self.playlist_last_menu.items = self.playlist_last_menu_list
        self.playlist_last_menu.open()

    def playlist_last_menu_set(self, playlist_id, youtube=False):
        self.playlist_last_menu.dismiss()
        self.text_playlist_last.text = playlist_id
        if youtube:
            self.load_in_thread(self.playlist_load, self.tracks_actions_show, load_arg=True, show_arg=True, show_arg2=True)
        else:
            self.load_in_thread(self.playlist_load, self.tracks_actions_show, show_arg=True, show_arg2=True)

    def format_change(self):
        self.format_mp3 = self.switch_format.active
        self.settings_save()

    def create_subfolders_change(self):
        self.create_subfolders = self.switch_create_subfolders.active
        self.settings_save()
    
    def music_folder_path_change(self):
        self.music_folder_path = self.text_music_folder_path.text
        self.settings_save()
    
    def file_manager_select(self, path):
        self.file_manager.close()
        self.text_music_folder_path.text = path
        self.music_folder_path_change()
    
    def file_manager_close(self, *args):
        self.file_manager.close()
    
    def save_lyrics_change(self):
        self.save_lyrics = self.switch_save_lyrics.active
        self.options_lyrics.height = int(self.save_lyrics) * 40
        self.options_lyrics.opacity = int(self.save_lyrics)
        self.settings_save()

    def lyrics_type_change(self):
        self.synchronized_lyrics = self.switch_lyrics_type.active
        self.settings_save()
    
    def webapi_enabled_change(self):
        self.webapi_enabled = self.switch_webapi_enabled.active
        if self.webapi_enabled and not self.webapi_watchdog.is_alive():
            self.webapi_server = WebApiServer()
            self.webapi_watchdog = Thread(target=self.watchdog_webapi, name="webapi_watchdog")
            self.webapi_watchdog.start()
        self.settings_save()

    def theme_toggle(self):
        if self.theme_cls.theme_style == "Light":
            self.theme_cls.theme_style = "Dark"
        else:
            self.theme_cls.theme_style = "Light"
        self.settings_save()
    
    def localization_menu_set(self, lang):
        self.localization_menu.dismiss()
        self.loc.set_lang(lang)
        self.text_localization.text = self.loc.get_lang()
        self.settings_save()
    
    def on_keyboard(self, window, key, scancode, codepoin, modifier):
        if key == 27:
            if self.screen_cur.name == "SpotifyScreen":
                if self.tab_cur.tab_name == "AlbumsTab":
                    self.tab_switch(self.artists_tab)
                elif self.tab_cur.tab_name == "TracksTab":
                    self.tab_switch(self.albums_tab)
            else:
                self.screen_switch("SpotifyScreen", "right")
            return True
        else:
            return False
    
    def settings_load(self):
        if os.path.exists(self.settings_file_path) and os.path.getsize(self.settings_file_path) > 0:
            with open(self.settings_file_path, "r") as settings_file:
                data = json.load(settings_file)
                self.music_folder_path = data["music_folder_path"]
                if "format_mp3" in data:
                    self.format_mp3 = data["format_mp3"]
                self.create_subfolders = data["create_subfolders"]
                if "save_lyrics" in data:
                    self.save_lyrics = data["save_lyrics"]
                if "synchronized_lyrics" in data:
                    self.synchronized_lyrics = data["synchronized_lyrics"]
                if "webapi_enabled" in data:
                    self.webapi_enabled = data["webapi_enabled"]
                self.theme_cls.theme_style = data["theme"]
                self.loc.set_lang(data["lang"])
                if "playlist_last" in data:
                    self.playlist_last = data["playlist_last"]
    
    def settings_save(self, notify=True):
        if notify:
            self.snackbar_show(self.loc.get("Settings saved"))
        with open(self.settings_file_path, "w") as settings_file:
            data = {
                "music_folder_path": self.music_folder_path,
                "format_mp3": self.format_mp3,
                "create_subfolders": self.create_subfolders,
                "save_lyrics": self.save_lyrics,
                "synchronized_lyrics": self.synchronized_lyrics,
                "webapi_enabled": self.webapi_enabled,
                "theme": self.theme_cls.theme_style,
                "lang": self.loc.get_lang(),
                "playlist_last": self.playlist_last
            }
            json.dump(data, settings_file)
        del self.s
        del self.y
        self.s = SpotifyLoader(self.loc.get_market(), self.music_folder_path, self.format_mp3, self.create_subfolders, self.label_loading_info, resource_find(".env"), resource_find("data/ytsfilter.json"), os.path.join(self.user_data_dir, ".cache"))
        self.y = YoutubeLoader(self.music_folder_path, self.format_mp3, self.create_subfolders, self.label_loading_info)

if __name__ == "__main__":
    os.environ["SSL_CERT_FILE"] = certifi.where()
    os.environ["KIVY_AUDIO"] = "ffpyplayer"
    if hasattr(sys, "_MEIPASS"):
        resource_add_path(os.path.join(sys._MEIPASS))
    app = Neodeemer()
    if platform == "android":
        from android.storage import primary_external_storage_path
        from android.permissions import Permission, request_permissions
        settings_folder_path = os.path.join(primary_external_storage_path(), app.loc.TITLE_R)
        request_permissions([Permission.WRITE_EXTERNAL_STORAGE, Permission.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS])
    else:
        settings_folder_path = app.user_data_dir
    if not os.path.exists(settings_folder_path):
        try:
            os.makedirs(settings_folder_path)
        except OSError:
            pass
    app.settings_file_path = os.path.join(settings_folder_path, "settings.json")
    try:
        app.settings_load()
    except OSError:
        pass
    app.run()
