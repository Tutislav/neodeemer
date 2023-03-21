import os
import sys
import tempfile
import unittest

sys.path.append(os.getcwd())
sys.path.append(os.path.abspath("neodeemer"))
if not os.path.exists("main.py"):
    os.chdir("neodeemer")
from neodeemer.songinfoloader import SpotifyLoader
from neodeemer.lyrics import KaraokeTexty, Musixmatch, Lyricsify, SpotifyLyricsApi

class TestLyrics(unittest.TestCase):
    music_folder_path = tempfile.mkdtemp()
    s = SpotifyLoader("CZ", music_folder_path, False, True)
    karaoketexty = KaraokeTexty()
    musixmatch = Musixmatch()
    lyricsify = Lyricsify()
    spotifylyricsapi = SpotifyLyricsApi()
    tracks = [
        { "name": "HIM Wicked Game", "track_dict": None, "karaoketexty": 1136, "musixmatch": 1299, "lyricsify": 1903, "spotifylyricsapi": 1787 },
        { "name": "Depeche Mode Enjoy the Silence", "track_dict": None, "karaoketexty": 732, "musixmatch": 735, "lyricsify": 771, "spotifylyricsapi": 1059 },
        { "name": "My Chemical Romance Teenagers", "track_dict": None, "karaoketexty": 1615, "musixmatch": 1601, "lyricsify": 1535, "spotifylyricsapi": 2079 },
        { "name": "Smash Mouth All Star", "track_dict": None, "karaoketexty": 2076, "musixmatch": 2250, "lyricsify": 3541, "spotifylyricsapi": 2990 },
        { "name": "Imagine Dragons Enemy", "track_dict": None, "karaoketexty": 2036, "musixmatch": 2020, "lyricsify": 2640, "spotifylyricsapi": 2706 }
    ]

    def test_a_spotifysearch(self):
        for track in self.tracks:
            results = self.s.tracks_search(track["name"])
            self.assertGreater(len(results), 0)
            track["track_dict"] = results[0]
    
    def test_b_lyrics(self):
        for track in self.tracks:
            try:
                lyrics = self.karaoketexty.find_lyrics(track["track_dict"])
            except:
                lyrics = ""
            self.assertEqual(len(lyrics), track["karaoketexty"])
            try:
                lyrics = self.musixmatch.find_lyrics(track["track_dict"])
            except:
                lyrics = ""
            self.assertEqual(len(lyrics), track["musixmatch"])
            try:
                lyrics = self.lyricsify.find_lyrics(track["track_dict"])
            except:
                lyrics = ""
            self.assertEqual(len(lyrics), track["lyricsify"])
            try:
                lyrics = self.spotifylyricsapi.find_lyrics(track["track_dict"])
            except:
                lyrics = ""
            self.assertEqual(len(lyrics), track["spotifylyricsapi"])

if __name__ == "__main__":
    unittest.main(verbosity=2)