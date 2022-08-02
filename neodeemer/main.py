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
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.properties import DictProperty
from kivy.resources import resource_add_path, resource_find
from kivy.uix.image import AsyncImage
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.utils import platform
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.filemanager import MDFileManager
from kivymd.uix.list import (IconLeftWidget, IconRightWidget, ILeftBody,
                             TwoLineAvatarIconListItem, TwoLineIconListItem)
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.tab import MDTabsBase
from plyer import notification

from download import Download
from localization import Localization
from songinfoloader import SpotifyLoader, YoutubeLoader
from tools import TrackStates, submit_bugs, track_file_state


__version__ = "0.3"

class Loading(MDFloatLayout):
    pass

class AsyncImageLeftWidget(ILeftBody, AsyncImage):
    pass

class ListLineArtist(TwoLineIconListItem):
    artist_dict = DictProperty()

class ListLineAlbum(TwoLineIconListItem):
    album_dict = DictProperty()

class ListLineTrack(TwoLineAvatarIconListItem):
    track_dict = DictProperty()

class WindowManager(ScreenManager):
    pass

class SpotifyScreen(Screen):
    pass

class ArtistsTab(MDBoxLayout, MDTabsBase):
    tab_name = "ArtistsTab"
    pass

class AlbumsTab(MDBoxLayout, MDTabsBase):
    tab_name = "AlbumsTab"
    pass

class TracksTab(MDBoxLayout, MDTabsBase):
    tab_name = "TracksTab"
    pass

class YoutubeScreen(Screen):
    pass

class SPlaylistScreen(Screen):
    pass

class YPlaylistScreen(Screen):
    pass

class SettingsScreen(Screen):
    pass

class Neodeemer(MDApp):
    icon = "data/icon.png"
    loc = Localization()
    create_subfolders = True
    selected_tracks = []
    download_queue = []
    download_queue_info = {
        "position": 0,
        "downloaded_b": 0,
        "total_b": 0
    }
    playlist_queue = []
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
        self.navigation_menu = self.root.ids.navigation_menu
        self.screen_manager = self.root.ids.screen_manager
        self.screens = [
            SpotifyScreen(name="SpotifyScreen"),
            YoutubeScreen(name="YoutubeScreen"),
            SPlaylistScreen(name="SPlaylistScreen"),
            YPlaylistScreen(name="YPlaylistScreen"),
            SettingsScreen(name="SettingsScreen")
        ]
        for screen in self.screens:
            self.screen_manager.add_widget(screen)
        Window.bind(on_keyboard=self.on_keyboard)
        self.screen_cur = self.screen_manager.current_screen
        self.toolbar = self.screen_cur.ids.toolbar
        self.progressbar = self.screen_cur.ids.progressbar
        self.artists_tab = self.screen_cur.ids.artists_tab
        self.albums_tab = self.screen_cur.ids.albums_tab
        self.tracks_tab = self.screen_cur.ids.tracks_tab
        self.file_manager = MDFileManager(exit_manager=self.file_manager_close, select_path=self.file_manager_select)
        if (platform == "android"):
            from android.permissions import Permission, request_permissions
            from android.storage import primary_external_storage_path
            try:
                self.music_folder_path
            except:
                self.music_folder_path = os.path.join(primary_external_storage_path(), "Music")
            self.file_manager_default_path = primary_external_storage_path()
            request_permissions([Permission.WRITE_EXTERNAL_STORAGE, Permission.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS])
        else:
            try:
                self.music_folder_path
            except:
                path = os.path.join(os.path.expanduser("~"), "Music")
                if not os.path.exists(path):
                    path = self.user_data_dir
                self.music_folder_path = path
            self.file_manager_default_path = os.path.expanduser("~")
        return
    
    def on_start(self):
        self.tab_switch(self.tracks_tab)
        self.loading = MDDialog(type="custom", content_cls=Loading(), md_bg_color=(0, 0, 0, 0))
        self.label_loading_info = self.loading.children[0].children[2].children[0].ids.label_loading_info
        self.s = SpotifyLoader(self.music_folder_path, self.create_subfolders, self.label_loading_info, self.loc.get_market())
        self.y = YoutubeLoader(self.music_folder_path, self.create_subfolders, self.label_loading_info)
        self.watchdog = Thread()
        self.play_track = Thread()
        for i in range(1, 6):
            globals()[f"download_tracks_{i}"] = Thread()
        self.text_playlist_last = self.screens[2].ids.text_splaylist_id
        self.playlist_last_menu_list = []
        self.playlist_last_menu = MDDropdownMenu(caller=self.text_playlist_last, items=self.playlist_last_menu_list, position="bottom", width_mult=20)
        self.check_create_subfolders = self.screens[4].ids.check_create_subfolders
        self.text_music_folder_path = self.screens[4].ids.text_music_folder_path
        self.text_localization = self.screens[4].ids.text_localization
        self.localization_menu_list = [
            {
                "viewclass": "OneLineListItem",
                "height": dp(50),
                "text": f"{lang}",
                "on_release": lambda x=lang:self.localization_menu_set(x)
            } for lang in self.loc.LANGUAGES.keys()
        ]
        self.localization_menu = MDDropdownMenu(caller=self.text_localization, items=self.localization_menu_list, position="auto", width_mult=2)
        self.submit_bug_dialog = MDDialog(
            title=self.loc.get("Submit bug"),
            text=self.loc.get("If some tracks has bad quality or even doesn't match the name you can submit it"),
            buttons=[
                MDFlatButton(text=self.loc.get("Submit bug"), on_press=lambda x:[submit_bugs(self.selected_tracks), self.submit_bug_dialog.dismiss()]),
                MDFlatButton(text=self.loc.get("Cancel"), on_press=lambda x:self.submit_bug_dialog.dismiss())
            ]
        )
    
    def screen_switch(self, screen_name, direction="left"):
        self.screen_manager.direction = direction
        self.screen_manager.current = screen_name
        self.screen_cur = self.screen_manager.current_screen
        self.toolbar = self.screen_cur.ids.toolbar
        self.progressbar = self.screen_cur.ids.progressbar
        self.progressbar_update()
        if (screen_name == "SettingsScreen"):
            if self.create_subfolders:
                self.check_create_subfolders.active = True
            else:
                self.check_create_subfolders.active = False
            self.text_music_folder_path.text = self.music_folder_path
            self.text_localization.text = self.loc.get_lang()
    
    def tab_switch(self, tab_instance):
        tabs = self.screen_manager.current_screen.ids.tabs
        tabs.switch_tab(tab_instance.tab_label)
        self.tab_cur = tab_instance
    
    def on_tab_switch(self, instance_tabs, instance_tab, instance_tab_label, tab_text):
        self.tab_cur = instance_tab
    
    def artists_load(self):
        text = self.artists_tab.ids.text_artists_search.text
        artists = self.s.artists_search(text)
        self.artists_tab.artists = artists
        if len(artists) > 0:
            return True
        else:
            return False
    
    def artists_show(self, *args):
        artists = self.artists_tab.artists
        mdlist_artists = self.artists_tab.ids.mdlist_artists
        mdlist_artists.clear_widgets()
        for artist in artists:
            if len(artist["artist_genres"]) > 0:
                secondary_text = str(artist["artist_genres"])
            else:
                secondary_text = " "
            line = ListLineArtist(text=artist["artist_name"], secondary_text=secondary_text, artist_dict=artist, on_press=lambda widget:self.load_in_thread(self.albums_load, self.albums_show, widget.artist_dict))
            line.add_widget(AsyncImageLeftWidget(source=artist["artist_image"]))
            mdlist_artists.add_widget(line)
    
    def albums_load(self, artist_dict=None):
        if artist_dict != None:
            albums = self.s.artist_albums(artist_dict)
        else:
            text = self.albums_tab.ids.text_albums_search.text
            albums = self.s.albums_search(text)
        self.albums_tab.albums = albums
        self.albums_tab.artist_dict = artist_dict
        if len(albums) > 0:
            return True
        else:
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
    
    def tracks_load(self, album_dict=None):
        if album_dict != None:
            tracks = self.s.album_tracks(album_dict)
        else:
            text = self.tracks_tab.ids.text_tracks_search.text
            tracks = self.s.tracks_search(text)
        self.tracks_tab.tracks = tracks
        self.tracks_tab.album_dict = album_dict
        if len(tracks) > 0:
            return True
        else:
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
    
    def youtube_load(self):
        text = self.screen_cur.ids.text_youtube_search.text
        tracks = self.y.tracks_search(text)
        self.screen_cur.tracks = tracks
        if len(tracks) > 0:
            return True
        else:
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
        self.settings_save(False)
        if len(tracks) > 0:
            label_playlist_info = self.screen_cur.ids.label_playlist_info
            label_playlist_info.text = "[b]" + tracks[0]["playlist_name"] + "[/b] - [b]" + str(len(tracks)) + "[/b]" + self.loc.get(" songs")
            return True
        else:
            return False
    
    def playlist_show(self, youtube=False, *args):
        tracks = self.screen_cur.tracks
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
    
    def load_in_thread(self, load_function, show_function=None, load_arg=None, show_arg=None, show_arg2=None):
        def load():
            if load_arg != None:
                show = load_function(load_arg)
            else:
                show = load_function()
            if show_function != None and show:
                if show_arg != None:
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
        if self.screen_cur.name == "SpotifyScreen":
            mdlist_tracks = self.tracks_tab.ids.mdlist_tracks
        else:
            mdlist_tracks = self.screen_cur.ids.mdlist_tracks
        self.mdlist_set_mode(mdlist_tracks, 0)
        for i in range(1, 6):
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
                sleep(randint(0, 20) / 100)
                if not track["locked"]:
                    track["locked"] = True
                    if any(state == track["state"] for state in [TrackStates.UNKNOWN, TrackStates.FOUND, TrackStates.SAVED]):
                        Download(track, self.s, self.download_queue_info).download_track()
                    track["locked"] = False
                else:
                    continue
            sleep(1)
    
    def play(self, widget):
        if not self.play_track.is_alive():
            self.play_track = Thread(target=self.track_play, args=[widget], name="play_track")
            self.play_track.start()
    
    def track_play(self, widget):
        Clock.schedule_once(self.loading.open)
        try:
            if (platform == "android"):
                track_dict = widget.parent.parent.parent.children[1].track_dict
                self.s.track_find_video_id(track_dict)
                from jnius import cast, autoclass
                PythonActivity = autoclass("org.kivy.android.PythonActivity")
                Intent = autoclass("android.content.Intent")
                Uri = autoclass("android.net.Uri")
                intent = Intent()
                intent.setAction(Intent.ACTION_VIEW)
                intent.setData(Uri.parse("https://youtu.be/" + track_dict["video_id"]))
                currentActivity = cast("android.app.Activity", PythonActivity.mActivity)
                currentActivity.startActivity(intent)
            else:
                if widget.children[0].icon == "play-circle-outline":
                    track_dict_temp = {}
                    track_dict_temp.update(widget.parent.parent.parent.children[1].track_dict)
                    if track_dict_temp["state"] != TrackStates.COMPLETED:
                        track_dict_temp["forcedmp3"] = False
                        track_dict_temp["folder_path"] = self.user_data_dir
                        track_dict_temp["file_path"] = os.path.join(self.user_data_dir, "temp.m4a")
                        track_dict_temp["file_path2"] = os.path.join(self.user_data_dir, "temp.mp3")
                        if "playlist_name" in track_dict_temp:
                            del track_dict_temp["playlist_name"]
                        if track_file_state(track_dict_temp) != TrackStates.COMPLETED:
                            download_queue_info_temp = {
                                "position": 0,
                                "downloaded_b": 0,
                                "total_b": 0
                            }
                            Download(track_dict_temp, self.s, download_queue_info_temp).download_track()
                            widget.parent.parent.parent.children[1].track_dict["video_id"] = track_dict_temp["video_id"]
                            widget.parent.parent.parent.children[1].track_dict["age_restricted"] = track_dict_temp["age_restricted"]
                            widget.parent.parent.parent.children[1].track_dict["state"] = TrackStates.FOUND
                    if self.sound != None:
                        self.sound.stop()
                        self.sound_prev_widget.children[0].icon = "play-circle-outline"
                    if track_dict_temp["forcedmp3"]:
                        file_path = track_dict_temp["file_path2"]
                    else:
                        file_path = track_dict_temp["file_path"]
                    self.sound = SoundLoader.load(file_path)
                    self.sound.play()
                    widget.children[0].icon = "stop-circle"
                    self.sound_prev_widget = widget
                elif self.sound != None:
                    self.sound.stop()
                    widget.children[0].icon = "play-circle-outline"
        except:
            Clock.schedule_once(partial(self.snackbar_show, self.loc.get("Error while playing track")))
        Clock.schedule_once(self.loading.dismiss)
    
    def watchdog_progress(self):
        for track in self.playlist_queue:
            Download(track, self.s, self.download_queue_info).playlist_file_save()
        while self.download_queue_info["position"] != len(self.download_queue):
            Clock.schedule_once(self.progressbar_update)
            sleep(0.5)
        self.progressbar_update()
        tracks_count = len(self.download_queue)
        self.download_queue = []
        self.download_queue_info["position"] = 0
        self.download_queue_info["downloaded_b"] = 0
        self.download_queue_info["total_b"] = 0
        self.playlist_queue = []
        if (platform == "win"):
            icon_path = resource_find("data/icon.ico")
        else:
            icon_path = resource_find("data/icon.png")
        notification.notify(title=self.loc.get("Download completed"), message=self.loc.get("Downloaded ") + str(tracks_count) + self.loc.get(" songs"), app_name=self.loc.TITLE, app_icon=icon_path)
    
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
    
    def mdlist_on_press(self, widget):
        widget.parent.parent.parent.do_selected_item()
    
    def mdlist_selected(self, instance_selection_list, instance_selection_item):
        self.toolbar.title = str(len(instance_selection_list.get_selected_list_items()))
        if not instance_selection_item.children[1].track_dict in self.selected_tracks:
            self.selected_tracks.append(instance_selection_item.children[1].track_dict)
    
    def mdlist_unselected(self, instance_selection_list, instance_selection_item):
        if instance_selection_list.get_selected_list_items():
            self.toolbar.title = str(len(instance_selection_list.get_selected_list_items()))
        else:
            self.toolbar.title = self.loc.TITLE
        if instance_selection_item.children[1].track_dict in self.selected_tracks:
            self.selected_tracks.remove(instance_selection_item.children[1].track_dict)
    
    def mdlist_set_mode(self, instance_selection_list, mode):
        if mode:
            bg_color = self.theme_cls.accent_color
            left_action_items = [
                ["close", lambda x:self.mdlist_set_mode(instance_selection_list, 0)],
                ["bug-outline", lambda x:self.submit_bug_dialog.open()]
            ]
            self.tracks_actions_show()
        else:
            bg_color = self.theme_cls.primary_color
            left_action_items = []
            instance_selection_list.unselected_all()
            self.tracks_actions_show(False)
        Animation(md_bg_color=bg_color, d=0.2).start(self.toolbar)
        self.toolbar.left_action_items = left_action_items
    
    def tracks_actions(self, action, youtube=False):
        if action == "download_all":
            if self.screen_cur.name == "SpotifyScreen":
                self.download(self.tracks_tab.tracks)
            else:
                self.download(self.screen_cur.tracks)
        elif action == "download_selected":
            self.download()
        elif action == "show":
            self.playlist_show(youtube)
    
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
        else:
            tracks_actions.opacity = 0
            tracks_actions.height = 0
    
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

    def create_subfolders_change(self):
        if self.check_create_subfolders.active:
            self.create_subfolders = True
        else:
            self.create_subfolders = False
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
                self.create_subfolders = data["create_subfolders"]
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
                "create_subfolders": self.create_subfolders,
                "theme": self.theme_cls.theme_style,
                "lang": self.loc.get_lang(),
                "playlist_last": self.playlist_last
            }
            json.dump(data, settings_file)
        del self.s
        del self.y
        self.s = SpotifyLoader(self.music_folder_path, self.create_subfolders, self.label_loading_info, self.loc.get_market())
        self.y = YoutubeLoader(self.music_folder_path, self.create_subfolders, self.label_loading_info)

if __name__ == "__main__":
    os.environ["SSL_CERT_FILE"] = certifi.where()
    os.environ["KIVY_AUDIO"] = "ffpyplayer"
    if hasattr(sys, '_MEIPASS'):
        resource_add_path(os.path.join(sys._MEIPASS))
        import ctypes
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 6)
    app = Neodeemer()
    app.settings_file_path = os.path.join(app.user_data_dir, "settings.json")
    app.settings_load()
    app.run()
