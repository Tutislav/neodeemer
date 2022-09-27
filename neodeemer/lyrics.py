from html.parser import HTMLParser
from urllib import parse, request

from tools import clean_track_name, contains_artist_track, norm


class Lyrics():
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
                if tag == "a":
                    if self.search_data in tag_last_value:
                        self.record = True
                        self.results.append({
                            "name": "",
                            "url": "https://www.karaoketexty.cz" + tag_value
                        })
            elif len(attrs) > 0:
                tag_value = attrs[0][1]
                if tag == "span" and tag_value == "album19_col2":
                    self.record2 = True
                elif tag == "a":
                    if self.search_data == "artist_tracks" and self.record2:
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
                if tag == "span":
                    if tag_value == "para_1lyrics_col1" or tag_value == "para_col1":
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
