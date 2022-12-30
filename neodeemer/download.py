import os
from html.parser import HTMLParser
from time import sleep
from urllib import request

import music_tag
import requests
from pytube import YouTube
from yt_dlp import YoutubeDL

from lyrics import Lyrics
from songinfoloader import SpotifyLoader
from tools import HEADERS, TrackStates


class Download():
    def __init__(self, track_dict: dict, spotifyloader: SpotifyLoader, download_queue_info: dict, save_lyrics: bool = True):
        self.track_dict = track_dict
        self.spotifyloader = spotifyloader
        self.download_queue_info = download_queue_info
        self.downloaded_bytes_prev = 0
        self.save_lyrics = save_lyrics
        if self.save_lyrics:
            self.lyrics = Lyrics()
        
    def download_on_progress(self, stream=None, chunk=None, bytes_remaining=None):
        if type(stream) is dict:
            chunk_size_b = stream["downloaded_bytes"] - self.downloaded_bytes_prev
            self.downloaded_bytes_prev = stream["downloaded_bytes"]
            self.download_queue_info["downloaded_b"] += chunk_size_b
        else:
            self.download_queue_info["downloaded_b"] += len(chunk)

    def total_b_add(self, size_b):
        if self.track_dict["track_size_b"] == None:
            self.track_dict["track_size_b"] = size_b
        if not self.track_dict["track_size_added"]:
            self.download_queue_info["total_b"] += self.track_dict["track_size_b"]
            self.track_dict["track_size_added"] = True
    
    def create_subfolders(self):
        if not os.path.exists(self.track_dict["folder_path"]):
            try:
                os.makedirs(self.track_dict["folder_path"])
            except OSError:
                pass

    def playlist_file_save(self):
        if "playlist_name" in self.track_dict:
            if self.track_dict["forcedmp3"]:
                file_path = self.track_dict["file_path2"]
            else:
                file_path = self.track_dict["file_path"]
            file_path = os.path.relpath(file_path, self.spotifyloader.music_folder_path)
            with open(self.track_dict["playlist_file_path"], "a+", encoding="utf-8") as playlist_file:
                playlist_file.seek(0)
                if not file_path + "\n" in playlist_file.readlines():
                    playlist_file.write(file_path + "\n")
    
    def save_tags(self):
        self.track_dict["state"] = TrackStates.TAGSAVING
        try:
            if self.track_dict["forcedmp3"]:
                file_path = self.track_dict["file_path2"]
            else:
                file_path = self.track_dict["file_path"]
            mtag = music_tag.load_file(file_path)
            mtag["artist"] = self.track_dict["artist_name2"]
            mtag["albumartist"] = self.track_dict["album_artist"]
            if len(self.track_dict["artist_genres"]) > 0:
                mtag["genre"] = self.track_dict["artist_genres"][0]
            mtag["album"] = self.track_dict["album_name"]
            mtag["totaltracks"] = self.track_dict["album_trackscount"]
            mtag["year"] = self.track_dict["album_year"]
            if len(self.track_dict["album_image"]) > 0:
                with request.urlopen(self.track_dict["album_image"]) as urldata:
                    mtag["artwork"] = urldata.read()
            mtag["tracktitle"] = self.track_dict["track_name"]
            mtag["tracknumber"] = self.track_dict["track_number"]
            mtag["comment"] = self.track_dict["video_id"]
            if self.save_lyrics:
                try:
                    mtag["lyrics"] = self.lyrics.find_lyrics(self.track_dict)
                except:
                    pass
            mtag.save()
        except:
            self.track_dict["state"] = TrackStates.FOUND
        else:
            self.track_dict["state"] = TrackStates.COMPLETED
            self.download_queue_info["position"] += 1
            self.playlist_file_save()

    def download_file(self, url, file_path):
        with open(file_path, "wb") as file:
            response = requests.get(url, headers=HEADERS, stream=True)
            self.total_b_add(len(response.content))
            for data in response.iter_content(4096):
                file.write(data)
                self.download_on_progress(chunk=data)

    def download_m4a_youtube_dl(self):
        video_url = "https://youtu.be/" + self.track_dict["video_id"]
        file_path_without_ext = self.track_dict["file_path"][:-4]
        params = {
            "format": "m4a/bestaudio",
            "outtmpl": file_path_without_ext + ".%(ext)s",
            "progress_hooks": [self.download_on_progress],
            "quiet": True,
            "postprocessor_args": ["-loglevel", "quiet"]
        }
        with YoutubeDL(params) as ydl:
            video_info = ydl.extract_info(video_url, False)
            self.total_b_add(video_info["filesize"])
            if video_info["ext"] != "m4a":
                self.track_dict["forcedmp3"] = True
            self.track_dict["state"] = TrackStates.DOWNLOADING
            if os.path.exists(self.track_dict["file_path"]):
                os.remove(self.track_dict["file_path"])
            elif os.path.exists(self.track_dict["file_path2"]):
                os.remove(self.track_dict["file_path2"])
            ydl.download([video_url])
            self.track_dict["state"] = TrackStates.SAVED
    
    def download_m4a_pytube(self):
        file_name = os.path.split(self.track_dict["file_path"])[1]
        youtube_video = YouTube("https://youtu.be/" + self.track_dict["video_id"], self.download_on_progress).streams.get_audio_only()
        self.total_b_add(int(youtube_video.filesize))
        self.track_dict["state"] = TrackStates.DOWNLOADING
        try:
            youtube_video.download(self.track_dict["folder_path"], file_name)
        except:
            self.download_file(youtube_video.url, self.track_dict["file_path"])
        self.track_dict["state"] = TrackStates.SAVED
    
    def download_mp3_neodeemer(self):
        mp3_url = "https://neodeemer.vorpal.tk/mp3.php?video_id=" + self.track_dict["video_id"]
        self.track_dict["state"] = TrackStates.DOWNLOADING
        self.download_file(mp3_url, self.track_dict["file_path2"])
        self.track_dict["state"] = TrackStates.SAVED

    def download_mp3_vevioz(self):
        class Mp3UrlParser(HTMLParser):
            list = []
            def handle_starttag(self, tag, attrs):
                if tag == "a":
                    for name, value in attrs:
                        if name == "href":
                            self.list.append(value)
            def to_list(self):
                return self.list
        url = "https://api.vevioz.com/@api/button/mp3/" + self.track_dict["video_id"]
        found_mp3_url = False
        while not found_mp3_url:
            try:
                with request.urlopen(request.Request(url, headers=HEADERS)) as urldata:
                    mp3urlparser = Mp3UrlParser()
                    mp3urlparser.feed(urldata.read().decode())
                    parser_attempt = 0
                    while len(mp3urlparser.to_list()) == 0:
                        parser_attempt += 1
                        if parser_attempt >= 5:
                            raise
                        sleep(0.5)
                    found_mp3_url = True
                    mp3_url = mp3urlparser.to_list()[2]
            except:
                sleep(2)
        self.track_dict["state"] = TrackStates.DOWNLOADING
        self.download_file(mp3_url, self.track_dict["file_path2"])
        self.track_dict["state"] = TrackStates.SAVED
    
    def download_track(self):
        self.create_subfolders()
        if self.track_dict["state"] == TrackStates.UNKNOWN and self.track_dict["video_id"] == None:
            self.spotifyloader.track_find_video_id(self.track_dict)
        if self.track_dict["state"] == TrackStates.FOUND:
            if not self.track_dict["forcedmp3"]:
                try:
                    self.download_m4a_youtube_dl()
                except:
                    try:
                        self.download_m4a_pytube()
                    except:
                        self.track_dict["forcedmp3"] = True
            else:
                try:
                    self.download_mp3_neodeemer()
                except:
                    self.download_mp3_vevioz()
        if self.track_dict["state"] == TrackStates.SAVED:
            self.save_tags()
        if self.track_dict["state"] == TrackStates.UNAVAILABLE:
            self.download_queue_info["position"] += 1
