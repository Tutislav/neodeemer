import json
import os
from datetime import datetime
from enum import Enum

import music_tag
import requests
import unidecode


class TrackStates(Enum):
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
    elif os.path.exists(track_dict["file_path2"]) and os.path.getsize(track_dict["file_path2"]) > 0:
        file_path = track_dict["file_path2"]
        track_dict["forcedmp3"] = True
    if file_path != None:
        try:
            mtag = music_tag.load_file(file_path)
            if (norm(mtag["artist"].value) == norm(track_dict["artist_name"]) and norm(mtag["tracktitle"].value) == norm(track_dict["track_name"])):
                if (track_dict["video_id"] != None):
                    if mtag["comment"].value == track_dict["video_id"]:
                        state = TrackStates.COMPLETED
                else:
                    state = TrackStates.COMPLETED
            else:
                state = TrackStates.SAVED
        except:
            state = TrackStates.SAVED
    return state

def submit_bug(track_dict):
    track_dict_temp = {}
    track_dict_temp.update(track_dict)
    del track_dict_temp["folder_path"]
    del track_dict_temp["file_path"]
    del track_dict_temp["file_path2"]
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
        if word_position > 0:
            if text[word_position - 1] == " ":
                contains = True
        if word_position + len(word) < len(text):
            if text[word_position + len(word)] == " ":
                contains = True
    if max_position != None:
        if word_position > max_position:
            contains = False
    return contains

def contains_date(text, compare_text=None):
    contains = False
    date_start_position = -1
    date_end_position = -1
    date_formats = [
        "%d/%m/%Y",
        "%d/%m/%y",
        "%d.%m.%Y",
        "%d.%m.%y"
    ]
    for i, char in enumerate(text):
        if char.isdigit():
            if date_start_position == -1:
                date_start_position = i
            else:
                date_end_position = i
            if date_end_position - date_start_position > 10:
                date_start_position = date_end_position
    if date_end_position - date_start_position > 5 and date_end_position - date_start_position < 11:
        date = text[date_start_position:date_end_position + 1]
        for date_format in date_formats:
            try:
                datetime.strptime(date, date_format)
                contains = True
            except:
                continue
        if compare_text != None:
            try:
                datetime.strptime(date, "%Y")
                if not date in compare_text:
                    contains = True
            except:
                pass
    return contains
