import json
import os
from datetime import datetime
from time import sleep
from urllib import request

import spotipy
from dotenv import load_dotenv
from pytube import Playlist as YoutubePlaylist
from spotipy.oauth2 import SpotifyClientCredentials
from yt_dlp import YoutubeDL
from youtube_search import YoutubeSearch
from ytmusicapi import YTMusic

from tools import (TrackStates, clean_track_name, contains_artist_track, contains_date, contains_separate_word, contains_part, mstostr, norm, strtoms,
                   track_file_state)


class MDLabel():
    text = ""

class SpotifyFix(spotipy.Spotify):
    artists_cache = {}

    def artist(self, artist: dict):
        if not artist["id"] in self.artists_cache:
            try:
                artist_dict = super().artist(artist["id"])
            except:
                artist_dict = {
                    "id": artist["id"],
                    "name": artist["name"],
                    "images": [],
                    "genres": []
                }
            self.artists_cache.update({artist["id"]: artist_dict})
        else:
            artist_dict = self.artists_cache[artist["id"]]
        return artist_dict

class Base():
    def __init__(self, music_folder_path: str, format_mp3: bool, create_subfolders: bool, label_loading_info: MDLabel = None):
        self.music_folder_path = music_folder_path
        self.format_mp3 = format_mp3
        self.create_subfolders = create_subfolders
        if label_loading_info != None:
            self.label_loading_info = label_loading_info
        else:
            self.label_loading_info = MDLabel()

class SpotifyLoader(Base):
    def __init__(self, market: str, music_folder_path: str, format_mp3: bool, create_subfolders: bool, label_loading_info: MDLabel = None, env_file_path: str = ".env", filter_file_path: str = "data/ytsfilter.json", cache_file_path: str = ".cache"):
        super().__init__(music_folder_path, format_mp3, create_subfolders, label_loading_info)
        if os.path.exists("env.env"):
            load_dotenv("env.env")
        else:
            load_dotenv(env_file_path)
        self.spotify = SpotifyFix(client_credentials_manager=SpotifyClientCredentials(cache_handler=spotipy.CacheFileHandler(cache_path=cache_file_path)))
        self.limit_small = 10
        self.limit = 50
        self.market = market
        self.filter_file_path = filter_file_path
        self.youtube_api_key = os.environ.get("YOUTUBE_API_KEY")
        self.load_filter()
    
    def load_filter(self):
        try:
            request.urlretrieve("https://raw.githubusercontent.com/Tutislav/neodeemer/main/neodeemer/data/ytsfilter.json", self.filter_file_path)
        except:
            pass
        if os.path.exists(self.filter_file_path):
            with open(self.filter_file_path, "r") as filter_file:
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

    def limit_offset(self, page):
        if page > 0:
            limit = self.limit_small
            offset = (page - 1) * 10
        else:
            limit = self.limit
            offset = 0
        return limit, offset

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
        elif album["release_date_precision"] == "month":
            album_year = datetime.strptime(album["release_date"], "%Y-%m").strftime("%Y")
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
            "spotify_id": track["id"],
            "forcedmp3": self.format_mp3,
            "reason": "",
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
            artists = self.spotify.search(artist_name, type="artist", limit=self.limit_small, market=self.market)
            artists = artists["artists"]["items"]
            for artist in artists:
                list.append(self.artist_to_dict(artist))
        return list
    
    def albums_search(self, album_name, page=0):
        list = []
        if len(album_name) > 0:
            limit, offset = self.limit_offset(page)
            albums = self.spotify.search(album_name, type="album", limit=limit, offset=offset, market=self.market)
            albums = albums["albums"]["items"]
            for album in albums:
                list.append(self.album_to_dict(album))
        return list
    
    def tracks_search(self, track_name, page=0):
        list = []
        if len(track_name) > 0:
            limit, offset = self.limit_offset(page)
            tracks = self.spotify.search(track_name, type="track", limit=limit, offset=offset, market=self.market)
            tracks = tracks["tracks"]["items"]
            for track in tracks:
                list.append(self.track_to_dict(track))
        return list
    
    def artist(self, artist_id):
        try:
            artist_dict = self.artist_to_dict(self.spotify.artist({"id": artist_id}))
        except:
            artist_dict = None
        return artist_dict
    
    def album(self, album_id):
        try:
            album_dict = self.album_to_dict(self.spotify.album(album_id, self.market))
        except:
            album_dict = None
        return album_dict
    
    def track(self, track_id):
        try:
            track_dict = self.track_to_dict(self.spotify.track(track_id, self.market))
        except:
            track_dict = None
        return track_dict

    def artist_albums(self, artist_dict, page=0):
        list = []
        limit, offset = self.limit_offset(page)
        albums = self.spotify.artist_albums(artist_dict["artist_id"], limit=limit, offset=offset)
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
    
    def video_get_details(self, video_dict):
        try:
            details_url = "https://youtube.googleapis.com/youtube/v3/videos?part=snippet,contentDetails&id=" + video_dict["id"] + "&key=" + self.youtube_api_key
            with request.urlopen(details_url) as urldata:
                details_data = json.loads(urldata.read().decode())
                video_description = details_data["items"][0]["snippet"]["description"]
                video_details = details_data["items"][0]["contentDetails"]
                video_dict["video_details"] = video_details
        except:
            video_url = "https://youtu.be/" + video_dict["id"]
            with YoutubeDL() as ydl:
                video_info = ydl.extract_info(video_url, False)
                video_description = video_info["description"]
        video_dict["video_description"] = norm(video_description)
    
    def track_find_video_id(self, track_dict):
        track_dict["state"] = TrackStates.SEARCHING
        options = self.ytsfilter["options"]
        preferred_channels = self.ytsfilter["preferred_channels"]
        excluded_channels = self.ytsfilter["excluded_channels"]
        excluded_words = self.ytsfilter["excluded_words"]
        artist_name2 = norm(track_dict["artist_name"])
        album_name2 = norm(track_dict["album_name"])
        track_name2 = norm(clean_track_name(track_dict["track_name"]))
        track_duration_s = track_dict["track_duration_ms"] / 1000
        max_results = 5
        text = track_dict["artist_name"] + " " + track_dict["track_name"]
        video_id = None
        try:
            with YTMusic() as ytmusic:
                tracks = ytmusic.search(text, "songs")
                if len(tracks) > 0:
                    track = tracks[0]
                    track_artist = norm(track["artists"][0]["name"])
                    track_name = norm(track["title"])
                    if contains_artist_track(track_artist, artist_name2):
                        if contains_artist_track(track_name, track_name=track_name2):
                            video_id = track["videoId"]
                if video_id == None:
                    album_text = track_dict["artist_name"] + " " + track_dict["album_name"]
                    albums = ytmusic.search(album_text, "albums")
                    if len(albums) > 0:
                        album = albums[0]
                        album_artist = norm(album["artists"][0]["name"])
                        album_name = norm(album["title"])
                        if contains_artist_track(album_artist, artist_name2):
                            if album_name2 in album_name or contains_part(album_name, album_name2):
                                album2 = ytmusic.get_album(album["browseId"])
                                tracks = album2["tracks"]
                                for track in tracks:
                                    track_name = norm(track["title"])
                                    if contains_artist_track(track_name, track_name=track_name2):
                                        contains_excluded = False
                                        for word in excluded_words:
                                            if word in track_name and not word in track_name2:
                                                if contains_separate_word(track_name, word):
                                                    contains_excluded = True
                                                    break
                                        if not contains_excluded:
                                            video_id = track["videoId"]
        except:
            pass
        while video_id == None and track_dict["state"] != TrackStates.UNAVAILABLE:
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
                if type(video["duration"]) is int:
                    video_duration_s = video["duration"]
                else:
                    video_duration_s = strtoms(video["duration"]) / 1000
                if type(video["views"]) is int:
                    video_views = video["views"]
                else:
                    video_views = video["views"].encode().decode("utf-8")
                    video_views = int("".join([c for c in video_views if c.isdigit()]).rstrip())
                video["video_channel"] = video_channel
                video["video_title"] = video_title
                video["video_description"] = ""
                video["video_details"] = ""
                if video_views > options["min_video_views"] and video_duration_s >= (track_duration_s - options["video_duration_tolerance_s"]) and video_duration_s <= (track_duration_s + options["video_duration_tolerance_s"]):
                    self.video_get_details(video)
                    video_description = video["video_description"]
                    video_details = video["video_details"]
                    if contains_artist_track(video_title, artist_name2, track_name2) or contains_artist_track(video_channel, artist_name2) or contains_artist_track(video_description, artist_name2):
                        if contains_artist_track(video_title, track_name=track_name2):
                            priority = 5
                            if track_name2 == artist_name2:
                                if not video_title.count(artist_name2) == 2:
                                    priority += options["not_same_name_penalization"]
                            if contains_date(video["title"], track_name2):
                                priority += options["contains_date_penalization"]
                            if any(word in video_channel for word in excluded_channels):
                                continue
                            for word in excluded_words:
                                if word in video_title and not word in track_name2:
                                    if contains_separate_word(video_title, word):
                                        priority += options["contains_word_title_penalization"]
                                        break
                                if word in video_description:
                                    if contains_separate_word(video_description, word, 100):
                                        priority += options["contains_word_description_penalization"]
                                        break
                            if "provided to youtube" in video["video_description"] or "taken from the album" in video["video_description"]:
                                priority += options["youtube_music_priority"]
                            elif artist_name2 in video["video_channel"] or any(word in video["video_channel"] for word in preferred_channels):
                                priority += options["prefered_channel_priority"]
                            elif artist_name2 in video["video_title"]:
                                priority += options["artist_in_title_priority"]
                            if priority > 0:
                                suitable_videos.append([video, priority])
            if len(suitable_videos) > 0:
                suitable_videos = sorted(suitable_videos, key=lambda x:x[1], reverse=True)
                video_id = suitable_videos[0][0]["id"]
            if video_id == None:
                if max_results < 10:
                    max_results = 10
                    continue
                if len(suitable_videos) > 0:
                    video_id = suitable_videos[0][0]["id"]
                else:
                    track_dict["reason"] = "Not available on YouTube"
                    track_dict["state"] = TrackStates.UNAVAILABLE
        if video_id != None:
            track_dict["video_id"] = video_id
            track_dict["state"] = TrackStates.FOUND
    
    def track_find_spotify_metadata(self, track_dict):
        if track_dict["state"] == TrackStates.FOUND and track_dict["artist_name"] == "":
            options = self.ytsfilter["options"]
            excluded_words = self.ytsfilter["excluded_words"]
            video_title = norm(track_dict["track_name"])
            video_channel = norm(track_dict["video_channel"])
            video_duration_s = track_dict["track_duration_ms"] / 1000
            tracks = self.tracks_search(track_dict["track_name"], 1)
            for track in tracks:
                artist_name2 = norm(track["artist_name"])
                track_name2 = norm(track["track_name"])
                track_duration_s = track["track_duration_ms"] / 1000
                if video_duration_s >= (track_duration_s - options["video_duration_tolerance_s"]) and video_duration_s <= (track_duration_s + options["video_duration_tolerance_s"]):
                    if contains_artist_track(video_title, artist_name2, track_name2) or contains_artist_track(video_channel, artist_name2):
                        if contains_artist_track(video_title, track_name=track_name2):
                            contains = False
                            for word in excluded_words:
                                if word in video_title and not word in track_name2:
                                        if contains_separate_word(video_title, word):
                                            contains = True
                            if contains:
                                continue
                            track["video_id"] = track_dict["video_id"]
                            track["state"] = track_dict["state"]
                            track["locked"] = track_dict["locked"]
                            contains, date = contains_date(track_dict["track_name"], track_name2)
                            if contains:
                                track["track_name"] = track["track_name"] + " (" + date + ")"
                                track["folder_path"] = track_dict["folder_path"]
                                track["file_path"] = track_dict["file_path"]
                                track["file_path2"] = track_dict["file_path2"]
                            track_dict.update(track)
                            break

class YoutubeLoader(Base):
    def track_to_dict(self, track, playlist=False):
        if not playlist:
            track_name = track["title"]
            if type(track["duration"]) is str:
                track_duration_ms = strtoms(track["duration"])
                track_duration_str = track["duration"]
            else:
                track_duration_ms = track["duration"] * 1000
                track_duration_str = mstostr(track["duration"] * 1000)
            video_id = track["id"]
            video_channel = track["channel"]
        else:
            track_name = track.title
            track_duration_ms = track.length * 1000
            track_duration_str = mstostr(track.length * 1000)
            video_id = track.video_id
            video_channel = track.author
        file_path = os.path.join(self.music_folder_path, norm(track_name, True, True) + ".m4a")
        file_path2 = os.path.join(self.music_folder_path, norm(track_name, True, True) + ".mp3")
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
            "track_duration_ms": track_duration_ms,
            "track_duration_str": track_duration_str,
            "track_number": 0,
            "track_size_b": None,
            "track_size_added": False,
            "video_id": video_id,
            "spotify_id": "",
            "forcedmp3": self.format_mp3,
            "reason": "",
            "folder_path": self.music_folder_path,
            "file_path": file_path,
            "file_path2": file_path2,
            "locked": False,
            "video_channel": video_channel
        }
        track_dict.update({"state": track_file_state(track_dict)})
        if track_dict["state"] != TrackStates.COMPLETED:
            track_dict["state"] = TrackStates.FOUND
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
