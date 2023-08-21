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


class TestPlaylistDownload(unittest.TestCase):
    music_folder_path = tempfile.mkdtemp()
    s = SpotifyLoader("CZ", music_folder_path, False, True)
    y = YoutubeLoader(music_folder_path, False, True)
    s_playlist_id = "https://open.spotify.com/playlist/37i9dQZF1DWXRqgorJj26U?si=5061e09bcd6a41cc"
    y_playlist_url = "https://www.youtube.com/playlist?list=PLvyEB5k0wSw6cy8ARt5c-VoyfNIe5udfd"
    tracks = []

    def test_a_spotifyplaylist(self):
        results = self.s.playlist_tracks(self.s_playlist_id)
        self.assertGreater(len(results), 0)
        self.tracks.extend(results[0:5])

    def test_b_youtubeplaylist(self):
        results = self.y.playlist_tracks(self.y_playlist_url)
        self.assertGreater(len(results), 0)
        self.tracks.extend(results[0:5])

    def test_c_find_video_id(self):
        for track in self.tracks:
            if track["state"].value == TrackStates.UNKNOWN.value and track["video_id"] == None:
                self.s.track_find_video_id(track)
            self.assertIsNot(track["video_id"], None)

    def test_d_download(self):
        for track in self.tracks:
            Download(track, self.s, None).download_track()
            self.assertEqual(track_file_state(track).value, TrackStates.COMPLETED.value, "Download error: " + str(track))

    def test_e_splaylist_file(self):
        with open(self.tracks[0]["playlist_file_path"], "r", encoding="utf-8") as playlist_file:
            paths = playlist_file.readlines()
            for path in paths:
                file_path = os.path.join(self.music_folder_path, path[:-1])
                self.assertTrue(os.path.exists(file_path))

    def test_f_yplaylist_file(self):
        with open(self.tracks[5]["playlist_file_path"], "r", encoding="utf-8") as playlist_file:
            paths = playlist_file.readlines()
            for path in paths:
                file_path = os.path.join(self.music_folder_path, path[:-1])
                self.assertTrue(os.path.exists(file_path))

    def test_z_cleanup(self):
        shutil.rmtree(self.music_folder_path)

if __name__ == "__main__":
    unittest.main(verbosity=2)