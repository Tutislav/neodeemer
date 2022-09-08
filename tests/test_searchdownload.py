import os
import shutil
import sys
import tempfile
import unittest

sys.path.append(os.getcwd())
sys.path.append(os.path.abspath("neodeemer"))
if not os.path.exists("main.py"):
    os.chdir("neodeemer")
from neodeemer.download import Download
from neodeemer.songinfoloader import SpotifyLoader, YoutubeLoader
from neodeemer.tools import TrackStates, track_file_state


class TestSearchDownload(unittest.TestCase):
    download_queue_info = {
        "position": 0,
        "downloaded_b": 0,
        "total_b": 0
    }
    music_folder_path = tempfile.mkdtemp()
    s = SpotifyLoader("CZ", music_folder_path, True)
    y = YoutubeLoader(music_folder_path, True)
    tracks_names = ["Jason Charles Miller Rules of Nature", "Morčata Na Útěku Outro", "Laura Branigan Self Control", "Dymytry Černí Andělé", "Imagine Dragons Enemy"]
    tracks = []

    def test_a_spotifysearch(self):
        for track_name in self.tracks_names:
            results = self.s.tracks_search(track_name)
            self.assertGreater(len(results), 0)
            self.tracks.append(results[0])

    def test_b_youtubesearch(self):
        for track_name in self.tracks_names:
            results = self.y.tracks_search(track_name)
            self.assertGreater(len(results), 0)
            self.tracks.append(results[0])

    def test_c_find_video_id(self):
        for track in self.tracks:
            if track["state"].value == TrackStates.UNKNOWN.value and track["video_id"] == None:
                self.s.track_find_video_id(track)
            self.assertIsNot(track["video_id"], None)

    def test_d_download(self):
        for track in self.tracks:
            Download(track, self.s, self.download_queue_info).download_track()
            self.assertEqual(track_file_state(track).value, TrackStates.COMPLETED.value)

    def test_z_cleanup(self):
        shutil.rmtree(self.music_folder_path)

if __name__ == "__main__":
    unittest.main(verbosity=2)