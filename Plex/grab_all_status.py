""" Grab all status from Plex """
#!/usr/bin/env python
import os
import json
import sys
import textwrap

from pathlib import Path
from datetime import datetime
from logs import setup_logger, plogger
from helpers import get_plex, get_xml_watched, get_xml_libraries, load_and_upgrade_env
from alive_progress import alive_bar

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
    sys.exit()

TARGET_URL_VAR = 'PLEX_URL'
plex_url = os.getenv(TARGET_URL_VAR)
if plex_url is None:
    TARGET_URL_VAR = 'PLEXAPI_AUTH_SERVER_BASEURL'
    plex_url = os.getenv(TARGET_URL_VAR)

TARGET_TOKEN_VAR = 'PLEX_TOKEN'
plex_token = os.getenv(TARGET_TOKEN_VAR)
if plex_token is None:
    TARGET_TOKEN_VAR = 'PLEXAPI_AUTH_SERVER_TOKEN'
    plex_token = os.getenv(TARGET_TOKEN_VAR)

if plex_url is None or plex_url == 'https://plex.domain.tld':
    plogger(f"You must specify {TARGET_URL_VAR} in the .env file.", 'info', 'a')
    sys.exit()

if plex_token is None or plex_token == 'PLEX-TOKEN':
    plogger(f"You must specify {TARGET_TOKEN_VAR} in the .env file.", 'info', 'a')
    sys.exit()

PLEX_OWNER = os.getenv("PLEX_OWNER")

LIBRARY_MAP = os.getenv("LIBRARY_MAP", "{}")

try:
    lib_map = json.loads(LIBRARY_MAP)
except: # pylint: disable=bare-except
    plogger("LIBRARY_MAP in the .env file appears to be broken.  Defaulting to an empty list.", 'info', 'a')
    lib_map = json.loads("{}")


def progress(count, total, status=""):
    """ Progress bar """
    bar_len = 40
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    p_bar = "=" * filled_len + "-" * (bar_len - filled_len)
    stat_str = textwrap.shorten(status, width=80)

    sys.stdout.write(f"[{p_bar}] {percents}% ... {stat_str.ljust(80)}\r")
    sys.stdout.flush()

def get_user_acct(acct_list, username): # pylint: disable=inconsistent-return-statements
    "" "Get the user account" ""
    for acct in acct_list:
        if acct.username == username:
            return acct

def get_data_line(username, p_type, section, video):
    """ Get the data line """
    file_line = ""
    content_rating = video['contentRating'] if 'contentRating' in video.keys() else 'NONE'
    episode_num = video['index'] if 'index' in video.keys() else video['duration']
    if p_type == "show":
        file_line = f"{username}\t{p_type}\t{section}\t{video['grandparentTitle']}\ts{video['parentIndex']:02}e{episode_num:02}\t{video['title']}"
    elif p_type == "movie":
        file_line = f"{username}\t{p_type}\t{section}\t{video['title']}\t{video['year']}\t{content_rating}"
    return file_line


def filter_for_unwatched(tgt_list):
    """ Filter for unwatched items """
    watched = [x for x in tgt_list if x.isPlayed]
    return watched

def process_section(username, section): # pylint: disable=inconsistent-return-statements
    """ Process a section """
    items = []
    file_string = ""

    print(f"------------ {section['title']} ------------")
    items = get_xml_watched(plex_url, plex_token, section['key'], section['type'])
    if len(items) > 0:
        with alive_bar(len(items), dual_line=True, title="Saving status") as a_bar:
            for video in items:
                status_text = get_data_line(username, section['type'], section['title'], video)
                file_string = f"{file_string}{status_text}{os.linesep}"
                a_bar() # pylint: disable=not-callable
        return file_string

PADWIDTH = 95
COUNT = 0
connected_plex_user = PLEX_OWNER
CONNECTED_PLEX_LIBRARY = ""

plex = get_plex()
PMI = plex.machineIdentifier

account = plex.myPlexAccount()
all_users = account.users()
ITEM = None
FILE_STRING = ""
DO_NOTHING = False

print(f"------------ {account.username} ------------")
try:
    # plex_sections = plex.library.sections()
    print("------------ getting libraries -------------")
    plex_sections = get_xml_libraries(plex_url, plex_token)

    if plex_sections is not None:
        for plex_section in plex_sections['MediaContainer']['Directory']:
            if not DO_NOTHING:
                if plex_section['type'] != "artist":
                    print(f"- processing {plex_section['type']} library: {plex_section['title']}")
                    STATUS_TEXT = process_section(account.username, plex_section)
                    FILE_STRING = f"{FILE_STRING}{STATUS_TEXT}{os.linesep}"
                else:
                    FILE_LINE = f"Skipping {plex_section['title']}"
                    print(FILE_LINE)
                    FILE_STRING = FILE_STRING + f"{FILE_LINE}{os.linesep}"
    else:
        print(f"Could not retrieve libraries for {account.username}")

except Exception as ex: # pylint: disable=broad-exception-caught
    FILE_LINE = f"Exception processing {account.username} - {ex}"
    print(FILE_LINE)
    FILE_STRING = FILE_STRING + f"{FILE_LINE}{os.linesep}"

user_ct = len(all_users)
USER_IDX = 0
for plex_user in all_users:
    user_acct = account.user(plex_user.title)
    USER_IDX += 1
    print(f"------------ {plex_user.title} {USER_IDX}/{user_ct} ------------")
    try:
        plex_token = user_acct.get_token(plex.machineIdentifier)
        print("------------ getting libraries -------------")
        plex_sections = get_xml_libraries(plex_url, plex_token)
        if plex_sections is not None:
            for plex_section in plex_sections['MediaContainer']['Directory']:
                if not DO_NOTHING:
                    if plex_section['type'] != "artist":
                        STATUS_TEXT = process_section(plex_user.title, plex_section)
                        FILE_STRING = f"{FILE_STRING}{STATUS_TEXT}{os.linesep}"
                    else:
                        FILE_LINE = f"Skipping {plex_section['title']}"
                        FILE_STRING = FILE_STRING + f"{FILE_LINE}{os.linesep}"
                        print(FILE_LINE)
        else:
            print(f"Could not retrieve libraries for {plex_user.title}")

    except Exception as ex: # pylint: disable=broad-exception-caught
        FILE_LINE = f"Exception processing {plex_user.title} - {ex}"
        FILE_STRING = FILE_STRING + f"{FILE_LINE}{os.linesep}"
        print(FILE_LINE)

print(f"{os.linesep}")
if len(FILE_STRING) > 0:
    with open("status.txt", "w", encoding="utf-8") as myfile:
        myfile.write(f"{FILE_STRING}{os.linesep}")
