import json
from html.parser import HTMLParser
from urllib import parse, request

from tools import HEADERS, clean_track_name, contains_artist_track, norm


class Lyrics():
    def __init__(self):
        self.karaoketexty = KaraokeTexty()
        self.musixmatch = Musixmatch()
        self.lyricsify = Lyricsify()
        self.spotifylyricsapi = SpotifyLyricsApi()

    def find_lyrics(self, track_dict: dict, synchronized: bool = False):
        lyrics = ""
        if synchronized:
            try:
                lyrics = self.spotifylyricsapi.find_lyrics(track_dict)
                if lyrics == "":
                    raise
            except:
                try:
                    lyrics = self.lyricsify.find_lyrics(track_dict)
                except:
                    lyrics = ""
        else:
            try:
                lyrics = self.musixmatch.find_lyrics(track_dict)
                if lyrics == "":
                    raise
            except:
                try:
                    lyrics = self.karaoketexty.find_lyrics(track_dict)
                except:
                    lyrics = ""
        return lyrics

class KaraokeTexty():
    def __init__(self):
        self.searchparser = self.SearchParser()
        self.lyricsparser = self.LyricsParser()
        self.search_url = "https://www.karaoketexty.cz/search?q="
        self.search_data_artist = "SERP-Artist"
        self.search_data_track = "SERP-Title"

    def search(self, q: str, type: str = "track"):
        q = parse.quote_plus(q)
        with request.urlopen(self.search_url + q) as urldata:
            self.searchparser.reset()
            self.searchparser.search_data = eval(f"self.search_data_{type}")
            self.searchparser.feed(urldata.read().decode())
        return self.searchparser.to_list()

    def get_artist_tracks(self, url: str):
        with request.urlopen(url) as urldata:
            self.searchparser.reset()
            self.searchparser.search_data = "artist_tracks"
            self.searchparser.feed(urldata.read().decode())
        return self.searchparser.to_list()

    def get_lyrics(self, url: str):
        with request.urlopen(url) as urldata:
            self.lyricsparser.reset()
            self.lyricsparser.feed(urldata.read().decode())
        return self.lyricsparser.to_str()

    def find_lyrics(self, track_dict: dict):
        lyrics = ""
        tracks = self.search(norm(clean_track_name(track_dict["track_name"])))
        for track in tracks:
            if contains_artist_track(track["name"], track_dict["artist_name2"], track_dict["track_name"]):
                lyrics = self.get_lyrics(track["url"])
                break
        if lyrics == "":
            artists = self.search(norm(track_dict["artist_name"]), "artist")
            for artist in artists:
                if contains_artist_track(artist["name"], track_dict["artist_name2"]):
                    tracks = self.get_artist_tracks(artist["url"])
                    for track in tracks:
                        if contains_artist_track(track["name"], track_name=track_dict["track_name"]):
                            lyrics = self.get_lyrics(track["url"])
                            break
        return lyrics

    class SearchParser(HTMLParser):
        results = []
        record = False
        record2 = False

        def handle_starttag(self, tag, attrs):
            if len(attrs) > 1:
                tag_value = attrs[0][1]
                tag_last_value = attrs[len(attrs) - 1][1]
                if tag == "a" and self.search_data in tag_last_value:
                    self.record = True
                    self.results.append({
                        "name": "",
                        "url": "https://www.karaoketexty.cz" + tag_value
                    })
            elif len(attrs) > 0:
                tag_value = attrs[0][1]
                if tag == "span" and tag_value == "album19_col2":
                    self.record2 = True
                elif tag == "a" and self.search_data == "artist_tracks" and self.record2:
                    self.record = True
                    self.record2 = False
                    self.results.append({
                        "name": "",
                        "url": "https://www.karaoketexty.cz" + tag_value
                    })

        def handle_data(self, data):
            if self.record:
                self.results[len(self.results) - 1]["name"] = data

        def handle_endtag(self, tag):
            if tag == "a" and self.record:
                self.record = False

        def to_list(self):
            return self.results

        def reset(self):
            super().reset()
            self.results = []
            self.record = False
            self.record2 = False

    class LyricsParser(HTMLParser):
        lyrics = ""
        record = False

        def handle_starttag(self, tag, attrs):
            if len(attrs) > 0:
                tag_value = attrs[0][1]
                if tag == "span" and (tag_value == "para_1lyrics_col1" or tag_value == "para_col1"):
                    self.record = True
                elif tag == "div" and "authors" in tag_value:
                    self.record = False

        def handle_data(self, data):
            if self.record:
                self.lyrics += data.lstrip().rstrip() + "\n"

        def handle_endtag(self, tag):
            if tag == "span" and self.record:
                self.lyrics += "\n"
                self.record = False

        def to_str(self):
            return self.lyrics.lstrip().rstrip()

        def reset(self):
            super().reset()
            self.lyrics = ""
            self.record = False

class Musixmatch():
    def __init__(self):
        self.searchparser = self.SearchParser()
        self.lyricsparser = self.LyricsParser()
        self.search_url = "https://www.musixmatch.com/search/{q}/tracks"
    
    def search(self, q: str):
        q = parse.quote(q)
        with request.urlopen(request.Request(self.search_url.format(q=q), headers=HEADERS)) as urldata:
            self.searchparser.reset()
            self.searchparser.feed(urldata.read().decode())
        return self.searchparser.to_list()

    def get_lyrics(self, url: str):
        with request.urlopen(request.Request(url, headers=HEADERS)) as urldata:
            self.lyricsparser.reset()
            self.lyricsparser.feed(urldata.read().decode())
        return self.lyricsparser.to_str()

    def find_lyrics(self, track_dict: dict):
        lyrics = ""
        tracks = self.search(norm(track_dict["artist_name"] + " " + clean_track_name(track_dict["track_name"])))
        for track in tracks:
            if contains_artist_track(track["artist"], track_dict["artist_name2"]):
                if contains_artist_track(track["name"], track_name=track_dict["track_name"]):
                    lyrics = self.get_lyrics(track["url"])
                    break
        return lyrics

    class SearchParser(HTMLParser):
        results = []
        record = False
        record2 = False

        def handle_starttag(self, tag, attrs):
            if len(attrs) > 1:
                tag_value = attrs[0][1]
                tag_last_value = attrs[len(attrs) - 1][1]
                if tag == "a" and tag_value == "title":
                    self.record = True
                    self.results.append({
                        "artist": "",
                        "name": "",
                        "url": "https://www.musixmatch.com" + tag_last_value
                    })
                elif tag == "a" and tag_value == "artist":
                    self.record2 = True

        def handle_data(self, data):
            if self.record:
                self.results[len(self.results) - 1]["name"] = data
            elif self.record2:
                self.results[len(self.results) - 1]["artist"] = data

        def handle_endtag(self, tag):
            if tag == "a" and (self.record or self.record2):
                self.record = False
                self.record2 = False

        def to_list(self):
            return self.results

        def reset(self):
            super().reset()
            self.results = []
            self.record = False
            self.record2 = False

    class LyricsParser(HTMLParser):
        lyrics = ""
        record = False

        def handle_starttag(self, tag, attrs):
            if len(attrs) > 0:
                tag_value = attrs[0][1]
                if tag == "div" and tag_value == "mxm-lyrics":
                    self.record = True
                elif tag == "span" and tag_value == "lyrics__content__ok":
                    self.record = True

        def handle_data(self, data):
            if self.record and self.lasttag == "span":
                self.lyrics += data.lstrip().rstrip() + "\n"

        def handle_endtag(self, tag):
            if (tag == "span" or tag == "div") and self.record:
                self.record = False

        def to_str(self):
            return self.lyrics.lstrip().rstrip()

        def reset(self):
            super().reset()
            self.lyrics = ""
            self.record = False

class Lyricsify():
    def __init__(self):
        self.searchparser = self.SearchParser()
        self.lyricsparser = self.LyricsParser()
        self.search_url = "https://www.lyricsify.com/lyrics/"

    def search(self, q: str):
        q = parse.quote_plus(q)
        with request.urlopen(request.Request(self.search_url + q, headers=HEADERS)) as urldata:
            self.searchparser.reset()
            self.searchparser.feed(urldata.read().decode())
        return self.searchparser.to_list()

    def get_lyrics(self, url: str):
        with request.urlopen(request.Request(url, headers=HEADERS)) as urldata:
            self.lyricsparser.reset()
            self.lyricsparser.feed(urldata.read().decode())
        return self.lyricsparser.to_str()

    def find_lyrics(self, track_dict: dict):
        lyrics = ""
        tracks = self.search(norm(track_dict["artist_name"] + " - " + clean_track_name(track_dict["track_name"])))
        for track in tracks:
            if contains_artist_track(track["name"], track_dict["artist_name2"], track_dict["track_name"]):
                lyrics = self.get_lyrics(track["url"])
                break
        return lyrics

    class SearchParser(HTMLParser):
        results = []
        record = False

        def handle_starttag(self, tag, attrs):
            if len(attrs) > 1:
                tag_value = attrs[0][1]
                tag_last_value = attrs[len(attrs) - 1][1]
                if tag == "a" and tag_last_value == "title":
                    self.record = True
                    self.results.append({
                        "name": "",
                        "url": "https://www.lyricsify.com" + tag_value
                    })

        def handle_data(self, data):
            if self.record:
                self.results[len(self.results) - 1]["name"] = data

        def handle_endtag(self, tag):
            if tag == "a" and self.record:
                self.record = False

        def to_list(self):
            return self.results

        def reset(self):
            super().reset()
            self.results = []
            self.record = False

    class LyricsParser(HTMLParser):
        lyrics = ""
        record = False

        def handle_starttag(self, tag, attrs):
            if len(attrs) > 0:
                tag_value = attrs[0][1]
                if tag == "div" and "details" in tag_value:
                    self.record = True
                elif tag == "div" and "lyricsonly" in tag_value:
                    self.record = False

        def handle_data(self, data):
            if self.record:
                self.lyrics += data.lstrip().rstrip() + "\n"

        def handle_endtag(self, tag):
            if tag == "div" and self.record:
                self.lyrics += "\n"
                self.record = False

        def to_str(self):
            return self.lyrics.lstrip().rstrip()

        def reset(self):
            super().reset()
            self.lyrics = ""
            self.record = False

class SpotifyLyricsApi():
    def __init__(self):
        self.lyrics_url = "https://spotify-lyric-api.herokuapp.com/?format=lrc&trackid="
    
    def find_lyrics(self, track_dict: dict):
        lyrics = ""
        with request.urlopen(self.lyrics_url + track_dict["track_id"]) as urldata:
            lyrics_data = json.loads(urldata.read().decode())
            if not lyrics_data["error"]:
                if lyrics_data["syncType"] == "LINE_SYNCED":
                    for line in lyrics_data["lines"]:
                        lyrics += "[" + line["timeTag"] + "]" + line["words"] + "\n"
        if lyrics != "":
            tags = "[ar:" + track_dict["artist_name"] + "]\n[al:" + track_dict["album_name"] + "]\n[ti:" + track_dict["track_name"] + "]\n"
            lyrics = tags + lyrics
        return lyrics
