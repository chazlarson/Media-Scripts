from plexapi.server import PlexServer
import os
import json
from dotenv import load_dotenv
from alive_progress import alive_bar

import sys
import textwrap

from helpers import get_all, get_plex, get_all_watched

import logging
from pathlib import Path
SCRIPT_NAME = Path(__file__).stem

logging.basicConfig(
    filename=f"{SCRIPT_NAME}.log",
    filemode="w",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logging.info(f"Starting {SCRIPT_NAME}")
print(f"Starting {SCRIPT_NAME}")

if os.path.exists(".env"):
    load_dotenv()
else:
    print(f"No environment [.env] file.  Exiting.")
    exit()

PLEX_URL = os.getenv("PLEX_URL")
PLEX_TOKEN = os.getenv("PLEX_TOKEN")
PLEX_OWNER = os.getenv("PLEX_OWNER")

LIBRARY_MAP = os.getenv("LIBRARY_MAP", "{}")

lib_map = json.loads(LIBRARY_MAP)


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
    if type == "show":
        file_line = f"{username}\t{type}\t{section}\t{video.grandparentTitle}\t{video.seasonEpisode}\t{video.title}"
    elif type == "movie":
        file_line = f"{username}\t{type}\t{section}\t{video.title}\t{video.year}\t{video.contentRating}"
    return file_line


def filter_for_unwatched(list):
    watched = [x for x in list if x.isPlayed]
    return watched


padwidth = 95
count = 0
connected_plex_user = PLEX_OWNER
connected_plex_library = ""

plex = get_plex(PLEX_URL, PLEX_TOKEN)
PMI = plex.machineIdentifier

account = plex.myPlexAccount()
all_users = account.users()
item = None
file_string = ""

print(f"------------ {account.username} ------------")
try:
    plex_sections = plex.library.sections()
    for plex_section in plex_sections:
        if plex_section.type != "artist":
            print(f"------------ {plex_section.title} ------------")
            the_lib = plex.library.section(plex_section.title)
            if plex_section.type == 'show':
                items = get_all(plex, the_lib, "episode", {'unwatched': False})
            else:
                items = get_all(plex, the_lib, None, {'unwatched': False})
            # watched_items = filter_for_unwatched(items)
            if len(items) > 0:
                with alive_bar(len(items), dual_line=True, title=f"Saving status") as bar:
                    for video in items:
                        status_text = get_data_line(account.username, plex_section.type, plex_section.title, video)
                        file_string = (
                            file_string
                            + status_text
                            + f"{os.linesep}"
                        )
                        bar()
        else:
            file_line = f"Skipping {plex_section.title}"
            print(file_line)
            file_string = file_string + f"{file_line}{os.linesep}"
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
        user_plex = get_plex(PLEX_URL, user_acct.get_token(plex.machineIdentifier))

        plex_sections = user_plex.library.sections()
        for plex_section in plex_sections:
            if plex_section.type != "artist":
                print(f"------------ {plex_section.title} ------------")
                the_lib = user_plex.library.section(plex_section.title)
                if plex_section.type == 'show':
                    items = get_all(plex, the_lib, "episode", {'unwatched': False})
                else:
                    items = get_all(plex, the_lib, None, {'unwatched': False})
                # watched_items = filter_for_unwatched(items)
                with alive_bar(len(items), dual_line=True, title=f"Saving status") as bar:
                    for video in items:
                        status_text = get_data_line(account.username, plex_section.type, plex_section.title, video)
                        file_string = (
                            file_string
                            + status_text
                            + f"{os.linesep}"
                        )
                        bar()
            else:
                file_line = f"Skipping {plex_section.title}"
                file_string = file_string + f"{file_line}{os.linesep}"
                print(file_line)
    except Exception as ex:
        file_line = f"Exception processing {plex_user.title} - {ex}"
        file_string = file_string + f"{file_line}{os.linesep}"
        print(file_line)

print(f"{os.linesep}")
if len(file_string) > 0:
    with open("status.txt", "w", encoding="utf-8") as myfile:
        myfile.write(f"{file_string}{os.linesep}")
