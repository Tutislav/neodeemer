[app]

# (str) Title of your application
title = Neodeemer

# (str) Package name
package.name = neodeemer

# (str) Package domain (needed for android/ios packaging)
package.domain = cz.tutislav

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,env,json

# (str) Application versioning (method 2)
version.regex = __version__ = ['"](.*)['"]
version.filename = %(source.dir)s/main.py

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3,certifi,charset-normalizer,docutils,ffpyplayer,idna,Kivy,kivymd,music-tag,mutagen,Pillow,git+https://github.com/kivy/plyer@master,Pygments,python-dotenv,git+https://github.com/JosiasAurel/pytube@patch-regex,requests,six,spotipy,Unidecode,urllib3,git+https://github.com/ytdl-org/youtube-dl@master,youtube-search

# (str) Presplash of the application
presplash.filename = %(source.dir)s/data/presplash.png

# (str) Icon of the application
icon.filename = %(source.dir)s/data/icon.png

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, REQUEST_IGNORE_BATTERY_OPTIMIZATIONS

# (int) Target Android API, should be as high as possible.
android.api = 29

# (int) Minimum API your APK / AAB will support.
android.minapi = 21

# (list) The Android archs to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
# In past, was `android.arch` as we weren't supporting builds for multiple archs at the same time.
android.archs = arm64-v8a, armeabi-v7a

# (bool) enables Android auto backup feature (Android API >=23)
android.allow_backup = True

# (str) Filename to the hook for p4a
p4a.hook = p4a/hook.py

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2