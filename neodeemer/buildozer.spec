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
requirements = python3,async-timeout==4.0.2,certifi==2022.5.18.1,charset-normalizer==2.1.1,Deprecated==1.2.13,docutils==0.19,ffpyplayer,idna==3.3,Kivy==2.1.0,kivymd==1.0.2,music-tag==0.4.3,mutagen==1.45.1,packaging==21.3,Pillow,git+https://github.com/kivy/plyer@master,Pygments==2.13.0,pyparsing==3.0.9,python-dotenv==0.20.0,git+https://github.com/JosiasAurel/pytube@patch-regex,redis==4.3.4,requests==2.28.1,six==1.16.0,spotipy==2.20.0,Unidecode==1.3.4,urllib3==1.26.12,wrapt==1.14.1,youtube-search==2.1.1,yt-dlp,ytmusicapi==0.22.0

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

# (str) Android NDK version to use
android.ndk = 19b

# (int) Android NDK API to use. This is the minimum API your app will support, it should usually match android.minapi.
android.ndk_api = 21

# (list) The Android archs to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
# In past, was `android.arch` as we weren't supporting builds for multiple archs at the same time.
android.archs = arm64-v8a, armeabi-v7a

# (bool) enables Android auto backup feature (Android API >=23)
android.allow_backup = True

# (str) python-for-android specific commit to use, defaults to HEAD, must be within p4a.branch
p4a.commit = 227a765

# (str) Filename to the hook for p4a
p4a.hook = p4a/hook.py

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2