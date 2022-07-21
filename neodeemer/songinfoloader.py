import json
import os
import sys
from datetime import datetime
from time import sleep
from urllib import request

import spotipy
from dotenv import load_dotenv
from kivy.resources import resource_find
from kivy.utils import platform
from kivymd.uix.label import MDLabel
from pytube import Playlist as YoutubePlaylist
from spotipy.oauth2 import SpotifyClientCredentials
from youtube_dl import YoutubeDL
from youtube_search import YoutubeSearch

from tools import (TrackStates, contains_separate_word, mstostr, norm, strtoms,
                   track_file_state)


class SpotifyFix(spotipy.Spotify):
    def artist(self, artist: dict):
        try:
            return super().artist(artist["id"])
        except:
            return {
                "id": artist["id"],
                "name": artist["name"],
                "images": [],
                "genres": []
            }

class Base():
    def __init__(self, music_folder_path: str, create_subfolders: bool, label_loading_info: MDLabel):
        self.music_folder_path = music_folder_path
        self.create_subfolders = create_subfolders
        self.label_loading_info = label_loading_info

class SpotifyLoader(Base):
    def __init__(self, music_folder_path: str, create_subfolders: bool, label_loading_info: MDLabel, market: str):
        super().__init__(music_folder_path, create_subfolders, label_loading_info)
        if platform == "android":
            load_dotenv("env.env")
        else:
            load_dotenv(resource_find(".env"))
        self.spotify = SpotifyFix(client_credentials_manager=SpotifyClientCredentials())
        self.limit = 50
        self.market = market
        self.youtube_api_key = os.environ.get("YOUTUBE_API_KEY")
        self.load_filter()
    
    def load_filter(self):
        if hasattr(sys, '_MEIPASS'):
            filter_file_path = os.path.join(sys._MEIPASS, "data", "ytsfilter.json")
        else:
            filter_file_path = resource_find("data/ytsfilter.json")
        try:
            request.urlretrieve("https://raw.githubusercontent.com/Tutislav/neodeemer/main/neodeemer/data/ytsfilter.json", filter_file_path)
        except:
            pass
        if os.path.exists(filter_file_path):
            with open(filter_file_path, "r") as filter_file:
                self.ytsfilter = json.load(filter_file)
    
    def select_image(self, images):
        if len(images) > 0:
            return images[0]["url"]
        else:
            return ""
    
    def artists_to_str(self, artists):
        str = ""
        if len(artists) > 1:
            for i, artist in enumerate(artists):
                str += artist["name"]
                if i < (len(artists) - 1):
                    str += "; "
        else:
            str = artists[0]["name"]
        return str

    def artist_to_dict(self, artist):
        return {
            "artist_id": artist["id"],
            "artist_name": artist["name"],
            "artist_genres": artist["genres"],
            "artist_image": self.select_image(artist["images"])
        }
    
    def album_to_dict(self, album, artist_dict=None):
        if artist_dict == None:
            artist = self.spotify.artist(album["artists"][0])
            artist_dict = self.artist_to_dict(artist)
        if album["release_date_precision"] == "day":
            album_year = datetime.strptime(album["release_date"], "%Y-%m-%d").strftime("%Y")
        else:
            album_year = album["release_date"]
        album_dict = {}
        album_dict.update(artist_dict)
        album_dict.update({
            "album_id": album["id"],
            "album_name": album["name"],
            "album_artist": self.artists_to_str(album["artists"]),
            "album_trackscount": album["total_tracks"],
            "album_year": album_year,
            "album_image": self.select_image(album["images"])
        })
        return album_dict
    
    def track_to_dict(self, track, album_dict=None):
        if album_dict == None:
            album_dict = self.album_to_dict(track["album"])
        if self.create_subfolders:
            folder_path = os.path.join(self.music_folder_path, norm(album_dict["artist_name"], True, True), norm(album_dict["album_name"], True, True))
            file_name = norm(track["name"], True, True)
        else:
            folder_path = self.music_folder_path
            file_name = norm(album_dict["artist_name"], True, True) + " - " + norm(track["name"], True, True)
        file_path = os.path.join(folder_path, file_name + ".m4a")
        file_path2 = os.path.join(folder_path, file_name + ".mp3")
        track_dict = {}
        track_dict.update(album_dict)
        track_dict.update({
            "artist_name": track["artists"][0]["name"],
            "artist_name2": self.artists_to_str(track["artists"]),
            "track_name": track["name"],
            "track_duration_ms": track["duration_ms"],
            "track_duration_str": mstostr(track["duration_ms"]),
            "track_number": track["track_number"],
            "track_size_b": None,
            "track_size_added": False,
            "video_id": None,
            "forcedmp3": False,
            "age_restricted": False,
            "folder_path": folder_path,
            "file_path": file_path,
            "file_path2": file_path2,
            "locked": False
        })
        track_dict.update({"state": track_file_state(track_dict)})
        return track_dict
    
    def artists_search(self, artist_name):
        list = []
        if len(artist_name) > 0:
            artists = self.spotify.search(artist_name, type="artist", limit=self.limit, market=self.market)
            artists = artists["artists"]["items"]
            for artist in artists:
                list.append(self.artist_to_dict(artist))
        return list
    
    def albums_search(self, album_name):
        list = []
        if len(album_name) > 0:
            albums = self.spotify.search(album_name, type="album", limit=self.limit, market=self.market)
            albums = albums["albums"]["items"]
            for album in albums:
                list.append(self.album_to_dict(album))
        return list
    
    def tracks_search(self, track_name):
        list = []
        if len(track_name) > 0:
            tracks = self.spotify.search(track_name, type="track", limit=self.limit, market=self.market)
            tracks = tracks["tracks"]["items"]
            for track in tracks:
                list.append(self.track_to_dict(track))
        return list
    
    def artist_albums(self, artist_dict):
        list = []
        albums = self.spotify.artist_albums(artist_dict["artist_id"], limit=self.limit)
        albums = albums["items"]
        for album in albums:
            list.append(self.album_to_dict(album, artist_dict))
        return list
    
    def album_tracks(self, album_dict):
        list = []
        tracks = self.spotify.album_tracks(album_dict["album_id"], limit=self.limit)
        tracks = tracks["items"]
        for track in tracks:
            list.append(self.track_to_dict(track, album_dict))
        return list
    
    def playlist_tracks(self, playlist_id):
        list = []
        if len(playlist_id) > 0:
            try:
                tracks2 = self.spotify.playlist(playlist_id, additional_types=("track",), market=self.market)
                playlist_name = tracks2["name"]
                playlist_file_path = os.path.join(self.music_folder_path, norm(playlist_name, True, True) + ".m3u")
                tracks = tracks2["tracks"]["items"]
                next = tracks2["tracks"]["next"]
                if next:
                    tracks2 = self.spotify.next(tracks2["tracks"])
                    tracks.extend(tracks2["items"])
                    next = tracks2["next"]
                while next:
                    tracks2 = self.spotify.next(tracks2)
                    tracks.extend(tracks2["items"])
                    next = tracks2["next"]
                position = 0
                for track in tracks:
                    track2 = track["track"]
                    track_dict = self.track_to_dict(track2)
                    track_dict.update({
                        "playlist_name": playlist_name,
                        "playlist_file_path": playlist_file_path
                    })
                    list.append(track_dict)
                    position += 1
                    self.label_loading_info.text = str(position).rjust(3)
                self.label_loading_info.text = ""
            except:
                pass
        return list
    
    def track_find_video_id(self, track_dict):
        track_dict["state"] = TrackStates.SEARCHING
        preferred_channels = self.ytsfilter["preferred_channels"]
        excluded_channels = self.ytsfilter["excluded_channels"]
        excluded_words = self.ytsfilter["excluded_words"]
        artist_name2 = norm(track_dict["artist_name"])
        track_name2 = norm(track_dict["track_name"])
        track_name3 = track_name2.split()
        track_duration_s = track_dict["track_duration_ms"] / 1000
        max_results = 4
        text = track_dict["artist_name"] + " " + track_dict["track_name"]
        video_id = None
        age_restricted = False
        while video_id == None:
            try:
                videos = YoutubeSearch(text, max_results=max_results).to_dict()
            except:
                sleep(2)
                continue
            else:
                if len(videos) == 0:
                    sleep(2)
                    continue
            suitable_videos = []
            for video in videos:
                video_channel = norm(video["channel"])
                video_title = norm(video["title"])
                video_duration_s = strtoms(video["duration"]) / 1000
                video_views = video["views"].encode().decode("utf-8")
                video_views = int("".join([c for c in video_views if c.isdigit()]).rstrip())
                video["video_channel"] = video_channel
                video["video_title"] = video_title
                video["video_description"] = ""
                video["video_details"] = ""
                if video_views > 300:
                    title_part_half = len(track_name3) / 2
                    title_part_count = 0
                    for word in track_name3:
                        if word in video_title:
                            title_part_count += 1
                    title_contains_part = title_part_count > title_part_half
                    if track_name2 in video_title or title_contains_part:
                        if track_name2 == artist_name2:
                            if not video_title.count(artist_name2) == 2:
                                continue
                        contains_excluded = False
                        for word in excluded_words:
                            if word in video_title and not word in track_name2 and not "official" in video_title:
                                if contains_separate_word(video_title, word):
                                    contains_excluded = True
                                    break
                        if contains_excluded:
                            continue
                        try:
                            details_url = "https://youtube.googleapis.com/youtube/v3/videos?part=snippet,contentDetails&id=" + video["id"] + "&key=" + self.youtube_api_key
                            with request.urlopen(details_url) as urldata:
                                details_data = json.loads(urldata.read().decode())
                                video_description = details_data["items"][0]["snippet"]["description"]
                                video_details = details_data["items"][0]["contentDetails"]
                                video["video_details"] = video_details
                                if "contentRating" in video_details:
                                    content_rating = video_details["contentRating"]
                                    if "ytRating" in content_rating:
                                        if content_rating["ytRating"] == "ytAgeRestricted":
                                            continue
                        except:
                            video_url = "https://youtu.be/" + self.track_dict["video_id"]
                            with YoutubeDL() as ydl:
                                video_info = ydl.extract_info(video_url, False)
                                video_description = video_info["description"]
                        video_description = norm(video_description)
                        video["video_description"] = video_description
                        if not artist_name2 in video_channel and not any(word in video_channel for word in preferred_channels):
                            if not "provide to youtube" in video_description and not "taken from the album" in video_description:
                                contains_excluded = False
                                for word in excluded_words:
                                    if word in video_description:
                                        if contains_separate_word(video_description, word, 100):
                                            contains_excluded = True
                                            break
                                if contains_excluded:
                                    continue
                        if video_duration_s >= (track_duration_s - 150) and video_duration_s <= (track_duration_s + 150) and not any(word in video_channel for word in excluded_channels):
                            suitable_videos.append(video)
            for video in suitable_videos:
                if "provided to youtube" in video["video_description"]:
                    video_id = video["id"]
                    break
            if video_id == None:
                for video in suitable_videos:
                    if any(word in video["video_channel"] for word in preferred_channels):
                        video_id = video["id"]
                        break
                    elif artist_name2 in video["video_channel"]:
                        video_id = video["id"]
                        break
                    elif "taken from the album" in video["video_description"]:
                        video_id = video["id"]
                        break
            if video_id == None:
                for video in suitable_videos:
                    if artist_name2 in video["video_title"]:
                        video_id = video["id"]
                        break
            if video_id == None:
                if max_results < 10:
                    max_results = 10
                    continue
                if len(suitable_videos) > 0:
                    video_id = suitable_videos[0]["id"]
                else:
                    video_id = videos[0]["id"]
                    video_details = videos[0]["video_details"]
                    if "contentRating" in video_details:
                        content_rating = video_details["contentRating"]
                        if "ytRating" in content_rating:
                            if content_rating["ytRating"] == "ytAgeRestricted":
                                age_restricted = True
        track_dict["video_id"] = video_id
        track_dict["age_restricted"] = age_restricted
        track_dict["state"] = TrackStates.FOUND

class YoutubeLoader(Base):
    def track_to_dict(self, track, playlist=False):
        if not playlist:
            track_name = track["title"]
            track_duration_str = track["duration"]
            video_id = track["id"]
            video_channel = track["channel"]
        else:
            track_name = track.title
            track_duration_str = mstostr(track.length * 1000)
            video_id = track.video_id
            video_channel = track.author
        file_path = os.path.join(self.music_folder_path, norm(track_name, True, True) + ".m4a")
        track_dict = {
            "artist_name": "",
            "artist_name2": "",
            "artist_genres": "",
            "album_name": "",
            "album_artist": "",
            "album_trackscount": 0,
            "album_year": 0,
            "album_image": "",
            "track_name": track_name,
            "track_duration_str": track_duration_str,
            "track_number": 0,
            "track_size_b": None,
            "track_size_added": False,
            "video_id": video_id,
            "forcedmp3": False,
            "age_restricted": False,
            "folder_path": self.music_folder_path,
            "file_path": file_path,
            "file_path2": file_path,
            "locked": False,
            "state": TrackStates.FOUND,
            "video_channel": video_channel
        }
        return track_dict
    
    def tracks_search(self, track_name):
        list = []
        if len(track_name) > 0:
            tracks = YoutubeSearch(track_name).to_dict()
            for track in tracks:
                list.append(self.track_to_dict(track))
        return list
    
    def playlist_tracks(self, playlist_url):
        list = []
        if len(playlist_url) > 0:
            try:
                tracks2 = YoutubePlaylist(playlist_url)
                playlist_name = tracks2.title
                playlist_file_path = os.path.join(self.music_folder_path, norm(playlist_name, True, True) + ".m3u")
                tracks = tracks2.videos
                position = 0
                for track in tracks:
                    track_dict = self.track_to_dict(track, True)
                    track_dict.update({
                        "playlist_name": playlist_name,
                        "playlist_file_path": playlist_file_path
                    })
                    list.append(track_dict)
                    position += 1
                    self.label_loading_info.text = str(position).rjust(3)
                self.label_loading_info.text = ""
            except:
                pass
        return list
