import os
import sys
import tempfile
import unittest

sys.path.append(os.getcwd())
sys.path.append(os.path.abspath("neodeemer"))
if not os.path.exists("main.py"):
    os.chdir("neodeemer")
from neodeemer.songinfoloader import SpotifyLoader
from neodeemer.lyrics import LRCLIB

class TestLyrics(unittest.TestCase):
    music_folder_path = tempfile.mkdtemp()
    s = SpotifyLoader("CZ", music_folder_path, False, True)
    lrclib = LRCLIB(0.0)
    tolerance = 10
    tracks = [
        { "name": "HIM Wicked Game", "track_dict": None, "lrclib": 1298 },
        { "name": "Depeche Mode Enjoy the Silence", "track_dict": None, "lrclib": 735 },
        { "name": "My Chemical Romance Teenagers", "track_dict": None, "lrclib": 1601 },
        { "name": "Smash Mouth All Star", "track_dict": None, "lrclib": 2250 },
        { "name": "Journey Dont Stop Believin", "track_dict": None, "lrclib": 1046 }
    ]

    def test_a_spotifysearch(self):
        for track in self.tracks:
            results = self.s.tracks_search(track["name"])
            self.assertGreater(len(results), 0)
            track["track_dict"] = results[0]
    
    def test_b_lyrics(self):
        for track in self.tracks:
            try:
                lyrics = self.lrclib.find_lyrics(track["track_dict"])
            except:
                lyrics = ""
            self.assertAlmostEqual(len(lyrics), track["lrclib"], delta=self.tolerance)

if __name__ == "__main__":
    unittest.main(verbosity=2)