import json
import os
from datetime import datetime
from enum import Enum

import music_tag
import requests
import unidecode


class TrackStates(Enum):
    UNAVAILABLE = -1
    UNKNOWN = 0
    SEARCHING = 1
    FOUND = 2
    DOWNLOADING = 3
    SAVED = 4
    TAGSAVING = 5
    COMPLETED = 6

HEADERS = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36"}

def norm(text, keepdiacritic=False, keepcase=False):
    text = "".join([c for c in text if c.isalpha() or c.isdigit() or c == " "]).rstrip()
    text = " ".join(text.split())
    if not keepdiacritic:
        text = unidecode.unidecode(text)
    if not keepcase:
        text = text.lower()
    return text

def clean_track_name(track_name):
    endings = ["original", "from", "remastered", "remake", "remaster", "music", "radio", "mix", "featuring", "new version"]
    track_name = track_name.lower()
    for ending in endings:
        if " - " in track_name and ending in track_name:
            if track_name.count(" - ") > 1:
                track_name = track_name[0:track_name.find(" - ", track_name.find(" - ") + 1)]
            else:
                track_name = track_name[0:track_name.find(" - ")]
    if " (" in track_name:
        track_name = track_name[0:track_name.find(" (")]
    return track_name

def mstostr(ms):
    min = round(ms / 1000 / 60)
    sec = round(ms / 1000 % 60)
    return str(min).zfill(2) + ":" + str(sec).zfill(2)

def strtoms(str):
    if str.count(":") == 1:
        colon_first = str.find(":")
        min = int(str[:colon_first])
        sec = int(str[colon_first + 1:])
        return (min * 60 + sec) * 1000
    else:
        colon_first = str.find(":")
        colon_second = str.find(":", colon_first + 1)
        hour = int(str[:colon_first])
        min = int(str[colon_first + 1:colon_second])
        sec = int(str[colon_second + 1:])
        return (hour * 60 * 60 + min * 60 + sec) * 1000

def track_file_state(track_dict):
    state = TrackStates.UNKNOWN
    file_path = None
    if os.path.exists(track_dict["file_path"]) and os.path.getsize(track_dict["file_path"]) > 0:
        file_path = track_dict["file_path"]
        track_dict["forcedmp3"] = False
    elif os.path.exists(track_dict["file_path2"]) and os.path.getsize(track_dict["file_path2"]) > 0:
        file_path = track_dict["file_path2"]
        track_dict["forcedmp3"] = True
    if file_path != None:
        try:
            mtag = music_tag.load_file(file_path)
            if (norm(mtag["artist"].value) == norm(track_dict["artist_name2"]) and norm(mtag["tracktitle"].value) == norm(track_dict["track_name"])):
                if (track_dict["video_id"] != None):
                    if mtag["comment"].value == track_dict["video_id"]:
                        state = TrackStates.COMPLETED
                else:
                    state = TrackStates.COMPLETED
            else:
                state = TrackStates.SAVED
        except:
            state = TrackStates.UNKNOWN
    return state

def submit_bug(track_dict):
    track_dict_temp = {}
    track_dict_temp.update(track_dict)
    del track_dict_temp["folder_path"]
    del track_dict_temp["file_path"]
    del track_dict_temp["file_path2"]
    if "playlist_name" in track_dict_temp:
        del track_dict_temp["playlist_name"]
        del track_dict_temp["playlist_file_path"]
    try:
        form_url = "https://docs.google.com/forms/d/e/1FAIpQLSfedpb4aVpMSyzjKMgmkQ1RZ9myBlMPpwo0OvVdpKrxd9nkvQ/formResponse"
        form_data = {
            "entry.634354352": track_dict_temp["artist_name"],
            "entry.1409540080": track_dict_temp["track_name"],
            "entry.1756305412": json.dumps(track_dict_temp, default=str)
        }
        requests.post(form_url, form_data, headers=HEADERS)
    except:
        pass

def submit_bugs(selected_tracks):
    for track in selected_tracks:
        submit_bug(track)

def contains_separate_word(text, word, max_position=None):
    contains = False
    if word in text:
        word_position = text.find(word)
        word_char_start = word_position - 1
        word_char_end = word_position + len(word)
        if word_position == 0:
            if word_char_end < len(text) and text[word_char_end] == " ":
                contains = True
        elif word_position == len(text) - len(word):
            if word_char_start >= 0 and text[word_char_start] == " ":
                contains = True
        else:
            if text[word_char_start] == " " and text[word_char_end] == " ":
                contains = True
    if max_position != None:
        if word_position > max_position:
            contains = False
    return contains

def contains_part(text, compare_text, compare_chars=False):
    contains = False
    text2 = text
    compare_text2 = compare_text.split()
    if compare_chars and len(compare_text2) <= 2:
        compare_text2 = []
        i = 0
        while i < len(compare_text) - 1:
            compare_text2.append(compare_text[i:i + 2])
            i += 2
        if len(compare_text) % 2 != 0:
            compare_text2.append(compare_text[len(compare_text) - 1])
        parts_half = len(compare_text2) * (2 / 3)
    else:
        parts_half = len(compare_text2) / 2
    parts_count = 0
    for word in compare_text2:
        if word in text2:
            text2 = text2[text2.find(word) + len(word):len(text2)]
            parts_count += 1
            contains = parts_count > parts_half
            if contains:
                break
    if not compare_chars and not contains and len(compare_text2) <= 2:
        contains = contains_part(text, compare_text, True)
    return contains

def contains_date(text, compare_text=None):
    contains = False
    date_start_position = -1
    date_end_position = -1
    date_formats = [
        "%d/%m/%Y",
        "%d/%m/%y",
        "%d.%m.%Y",
        "%d.%m.%y",
        "%d %b %Y",
        "%d %B %Y",
        "%m.%d.%Y",
        "%m.%d.%y",
        "%Y-%m-%d",
        "%y-%m-%d",
        "%Y/%m/%d",
        "%y/%m/%d"
    ]
    dates = []
    for i, char in enumerate(text):
        if char.isdigit():
            if date_start_position == -1:
                date_start_position = i
            else:
                date_end_position = i
            if date_end_position - date_start_position > 10:
                date_start_position = date_end_position
        elif all(char != c for c in ["/", ".", "-", " "]) and date_end_position - date_start_position > 2:
            dates.append(text[date_start_position:date_end_position + 1])
            date_start_position = date_end_position
        if date_end_position == (len(text) - 1) and date_end_position - date_start_position > 2:
            dates.append(text[date_start_position:date_end_position + 1])
    if len(dates) > 0:
        for date in dates:
            for date_format in date_formats:
                try:
                    parsed_date = datetime.strptime(date, date_format)
                    if parsed_date <= datetime.now():
                        contains = True
                        break
                except:
                    continue
            if compare_text != None:
                try:
                    parsed_date = datetime.strptime(date, "%Y")
                    if not date in compare_text:
                        if parsed_date <= datetime.now():
                            contains = True
                except:
                    pass
        return contains, dates[0]
    else:
        return contains, None

def contains_artist_track(text, artist_name=None, track_name=None):
    contains = False
    if " - " in text:
        text2 = text.split(" - ")
        text_artist = norm(text2[0])
        text_track = norm(clean_track_name(text2[1]))
    else:
        text = norm(clean_track_name(text))
        text_artist = text
        text_track = text
    if artist_name != None:
        if "; " in artist_name:
            artists = artist_name.split("; ")
        else:
            artists = [norm(artist_name)]
    else:
        artists = [""]
    if track_name != None:
        track_name = norm(clean_track_name(track_name))
    else:
        track_name = ""
    for artist in artists:
        artist = norm(artist)
        if artist in text_artist or contains_part(text_artist, artist):
            if track_name in text_track or contains_part(text_track, track_name):
                contains = True
                break
    return contains

def open_url(url, platform):
    if platform == "android":
        from jnius import cast, autoclass
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        Intent = autoclass("android.content.Intent")
        Uri = autoclass("android.net.Uri")
        intent = Intent()
        intent.setAction(Intent.ACTION_VIEW)
        intent.setData(Uri.parse(url))
        currentActivity = cast("android.app.Activity", PythonActivity.mActivity)
        currentActivity.startActivity(intent)
    else:
        import webbrowser
        webbrowser.open(url)

def check_update_available(current_version):
    url = "https://api.github.com/repos/Tutislav/neodeemer/releases"
    urldata = requests.get(url)
    data = urldata.json()
    new_version = data[0]["tag_name"]
    return new_version != current_version

def check_mp3_available(track_dict):
    url = "https://neodeemer.vorpal.tk/mp3.php?video_id=" + track_dict["video_id"] + "&info=1"
    urldata = requests.get(url)
    return bool(int(urldata.text))

def font(text: str):
    text = "[font=Regular]" + text + "[/font]"
    return text
