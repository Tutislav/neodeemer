[<img src="neodeemer/data/icon.png" alt="Icon" height="100" align="right">](https://github.com/Tutislav/neodeemer/releases/latest)

# Neodeemer
[![GitHub all releases](https://img.shields.io/github/downloads/Tutislav/neodeemer/total)](https://github.com/Tutislav/neodeemer/releases/latest)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/Tutislav/neodeemer)](https://github.com/Tutislav/neodeemer/releases/latest)
[![GitHub](https://img.shields.io/github/license/Tutislav/neodeemer)](https://github.com/Tutislav/neodeemer/blob/main/LICENSE)

Multiplatform music downloader with option to download whole albums and Spotify/YouTube playlists.\
Available on **Android**, **Windows** and [**Linux***](#running-from-source "You must run it from source").

## **[▶Download latest release◀](https://github.com/Tutislav/neodeemer/releases/latest)**

## Features
- Search music on Spotify/YouTube
- Play songs before you download it
- Download single songs or whole albums
- Download whole Spotify/YouTube playlist with `.m3u` file
- It will automatically save track name, artist name, album image and other tags to songs (only Spotify)

## Screenshots
<picture>
    <source media="(prefers-color-scheme: light)" srcset="img/neodeemer_screenshot_1_light.jpg">
    <img src="img/neodeemer_screenshot_1.jpg" alt="Screenshot 1">
</picture>
<picture>
    <source media="(prefers-color-scheme: light)" srcset="img/neodeemer_screenshot_2_light.jpg">
    <img src="img/neodeemer_screenshot_2.jpg" alt="Screenshot 2">
</picture>
<picture>
    <source media="(prefers-color-scheme: light)" srcset="img/neodeemer_screenshot_3_light.jpg">
    <img src="img/neodeemer_screenshot_3.jpg" alt="Screenshot 3">
</picture>
<picture>
    <source media="(prefers-color-scheme: light)" srcset="img/neodeemer_screenshot_4_light.jpg">
    <img src="img/neodeemer_screenshot_4.jpg" alt="Screenshot 4">
</picture>

## Running from source
1. Install Python 3.8.10 or later if you don't have it already
2. Clone this repo
3. Get your own [Spotify](https://developer.spotify.com/dashboard/) and [YouTube](https://developers.google.com/youtube/v3/getting-started) API keys
4. Create `.env` file in `neodeemer\neodeemer` (folder where is main.py) like this:
    ```
    SPOTIPY_CLIENT_ID=
    SPOTIPY_CLIENT_SECRET=
    YOUTUBE_API_KEY=
    ```
5. Continue depending on your platform
### Windows
```
cd neodeemer\neodeemer
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```
### Linux
```
cd neodeemer/neodeemer
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

## Issues
If encounter some tracks, that has bad quality or even doesn't match the name, you can submit it directly in the app using
<picture>
    <source media="(prefers-color-scheme: light)" srcset="img/bug_outline_light.png">
    <img src="img/bug_outline.png" alt="Bug icon">
</picture>
icon, when you select track.\
If you have other issue or some idea to make the app better, just open a new issue on GitHub.

## Acknowledgments
- [Kivy](https://kivy.org/)
- [KivyMD](https://github.com/kivymd/KivyMD)
- [Spotipy](https://github.com/plamere/spotipy)
- [youtube_search](https://github.com/joetats/youtube_search)
- [ytmusicapi](https://github.com/sigma67/ytmusicapi)
- [pytube](https://github.com/pytube/pytube)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [music-tag](https://github.com/KristoforMaynard/music-tag)
- [FFPyPlayer](https://github.com/matham/ffpyplayer)
- [Plyer](https://github.com/kivy/plyer)
- [python-dotenv](https://github.com/theskumar/python-dotenv)
- [Requests](https://github.com/psf/requests)
- [Unidecode](https://github.com/avian2/unidecode)
- [Certifi](https://github.com/certifi/python-certifi)