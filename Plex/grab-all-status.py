#!/usr/bin/env python
from plexapi.server import PlexServer
import os
import json
from dotenv import load_dotenv
from alive_progress import alive_bar

import sys
import textwrap

from helpers import get_all_from_library, get_plex, get_all_watched, get_xml, get_xml_watched, get_media_details, get_xml_libraries, load_and_upgrade_env

from logs import setup_logger, plogger, blogger, logger
from pathlib import Path
from datetime import datetime, timedelta
# current dateTime
now = datetime.now()

# convert to string
RUNTIME_STR = now.strftime("%Y-%m-%d %H:%M:%S")

SCRIPT_NAME = Path(__file__).stem

VERSION = "0.1.1"

# DONE 0.1.1: guard against empty library map

env_file_path = Path(".env")

ACTIVITY_LOG = f"{SCRIPT_NAME}.log"
setup_logger('activity_log', ACTIVITY_LOG)

plogger(f"Starting {SCRIPT_NAME} {VERSION} at {RUNTIME_STR}", 'info', 'a')

if load_and_upgrade_env(env_file_path) < 0:
    exit()

target_url_var = 'PLEX_URL'
PLEX_URL = os.getenv(target_url_var)
if PLEX_URL is None:
    target_url_var = 'PLEXAPI_AUTH_SERVER_BASEURL'
    PLEX_URL = os.getenv(target_url_var)

target_token_var = 'PLEX_TOKEN'
PLEX_TOKEN = os.getenv(target_token_var)
if PLEX_TOKEN is None:
    target_token_var = 'PLEXAPI_AUTH_SERVER_TOKEN'
    PLEX_TOKEN = os.getenv(target_token_var)

if PLEX_URL is None or PLEX_URL == 'https://plex.domain.tld':
    plogger(f"You must specify {target_url_var} in the .env file.", 'info', 'a')
    exit()

if PLEX_TOKEN is None or PLEX_TOKEN == 'PLEX-TOKEN':
    plogger(f"You must specify {target_token_var} in the .env file.", 'info', 'a')
    exit()

PLEX_OWNER = os.getenv("PLEX_OWNER")

LIBRARY_MAP = os.getenv("LIBRARY_MAP", "{}")

try:
    lib_map = json.loads(LIBRARY_MAP)
except:
    plogger(f"LIBRARY_MAP in the .env file appears to be broken.  Defaulting to an empty list.", 'info', 'a')
    lib_map = json.loads("{}")


def progress(count, total, status=""):
    bar_len = 40
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = "=" * filled_len + "-" * (bar_len - filled_len)
    stat_str = textwrap.shorten(status, width=80)

    sys.stdout.write("[%s] %s%s ... %s\r" % (bar, percents, "%", stat_str.ljust(80)))
    sys.stdout.flush()


def get_user_acct(acct_list, username):
    for acct in acct_list:
        if acct.username == username:
            return acct


def get_data_line(username, type, section, video):
    file_line = ""
    contentRating = video['contentRating'] if 'contentRating' in video.keys() else 'NONE'
    episodeNum = video['index'] if 'index' in video.keys() else video['duration']
    if type == "show":
        file_line = f"{username}\t{type}\t{section}\t{video['grandparentTitle']}\ts{video['parentIndex']:02}e{episodeNum:02}\t{video['title']}"
    elif type == "movie":
        file_line = f"{username}\t{type}\t{section}\t{video['title']}\t{video['year']}\t{contentRating}"
    return file_line


def filter_for_unwatched(list):
    watched = [x for x in list if x.isPlayed]
    return watched

def process_section(username, section):
    items = []
    file_string = ""

    print(f"------------ {section['title']} ------------")
    items = get_xml_watched(PLEX_URL, PLEX_TOKEN, section['key'], section['type'])
    if len(items) > 0:
        with alive_bar(len(items), dual_line=True, title=f"Saving status") as bar:
            for video in items:
                status_text = get_data_line(username, section['type'], section['title'], video)
                file_string = (f"{file_string}{status_text}{os.linesep}")
                bar()
    return file_string

padwidth = 95
count = 0
connected_plex_user = PLEX_OWNER
connected_plex_library = ""

plex = get_plex()
PMI = plex.machineIdentifier

account = plex.myPlexAccount()
all_users = account.users()
item = None
file_string = ""
DO_NOTHING = False

print(f"------------ {account.username} ------------")
try:
    # plex_sections = plex.library.sections()
    print(f"------------ getting libraries -------------")
    plex_sections = get_xml_libraries(PLEX_URL, PLEX_TOKEN)

    if plex_sections is not None:
        for plex_section in plex_sections['MediaContainer']['Directory']:
            if not DO_NOTHING:
                if plex_section['type'] != "artist":
                    print(f"- processing {plex_section['type']} library: {plex_section['title']}")
                    status_text = process_section(account.username, plex_section)
                    file_string = (f"{file_string}{status_text}{os.linesep}")
                else:
                    file_line = f"Skipping {plex_section['title']}"
                    print(file_line)
                    file_string = file_string + f"{file_line}{os.linesep}"
    else:
        print(f"Could not retrieve libraries for {account.username}")
        
except Exception as ex:
    file_line = f"Exception processing {account.username} - {ex}"
    print(file_line)
    file_string = file_string + f"{file_line}{os.linesep}"

user_ct = len(all_users)
user_idx = 0
for plex_user in all_users:
    user_acct = account.user(plex_user.title)
    user_idx += 1
    print(f"------------ {plex_user.title} {user_idx}/{user_ct} ------------")
    try:
        PLEX_TOKEN = user_acct.get_token(plex.machineIdentifier)
        print(f"------------ getting libraries -------------")
        plex_sections = get_xml_libraries(PLEX_URL, PLEX_TOKEN)
        if plex_sections is not None:
            for plex_section in plex_sections['MediaContainer']['Directory']:
                if not DO_NOTHING:
                    if plex_section['type'] != "artist":
                        status_text = process_section(plex_user.title, plex_section)
                        file_string = (f"{file_string}{status_text}{os.linesep}")
                    else:
                        file_line = f"Skipping {plex_section['title']}"
                        file_string = file_string + f"{file_line}{os.linesep}"
                        print(file_line)
        else:
            print(f"Could not retrieve libraries for {plex_user.title}")

    except Exception as ex:
        file_line = f"Exception processing {plex_user.title} - {ex}"
        file_string = file_string + f"{file_line}{os.linesep}"
        print(file_line)

print(f"{os.linesep}")
if len(file_string) > 0:
    with open("status.txt", "w", encoding="utf-8") as myfile:
        myfile.write(f"{file_string}{os.linesep}")
