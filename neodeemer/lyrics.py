import requests


class Lyrics():
    def __init__(self, app_version: float):
        self.lrclib = LRCLIB(app_version)

    def find_lyrics(self, track_dict: dict, synchronized: bool = False):
        lyrics = self.lrclib.find_lyrics(track_dict, synchronized)
        return lyrics

class LRCLIB():
    def __init__(self, app_version: float):
        self.HEADERS = {"user-agent": "Neodeemer " + str(app_version) + " (https://github.com/Tutislav/neodeemer)"}
        self.get_url = "https://lrclib.net/api/get?artist_name={artist_name}&album_name={album_name}&track_name={track_name}&duration={duration}"
    
    def find_lyrics(self, track_dict: dict, synchronized: bool = False):
        lyrics = ""
        track_duration_s = int(track_dict["track_duration_ms"] / 1000)
        url = self.get_url.format(artist_name=track_dict["artist_name"], album_name=track_dict["album_name"], track_name=track_dict["track_name"], duration=track_duration_s)
        urldata = requests.get(url, headers=self.HEADERS)
        data = urldata.json()
        if "statusCode" in data and data["statusCode"] == 404:
            lyrics = ""
        elif "syncedLyrics" in data:
            if synchronized:
                if len(data["syncedLyrics"]) > 0:
                    lyrics = data["syncedLyrics"]
            else:
                if len(data["plainLyrics"]) > 0:
                    lyrics = data["plainLyrics"]
        return lyrics
