""" Mark all items in the status.txt file as watched in the appropriate Plex library """
#!/usr/bin/env python
import json
import os
import re
import sys
import textwrap
from pathlib import Path
from datetime import datetime
from helpers import get_plex, load_and_upgrade_env

from logs import setup_logger, plogger

SCRIPT_NAME = Path(__file__).stem

# DONE 0.1.1: guard against empty library map
# DONE 0.1.2: pylint fixes

VERSION = "0.1.2"

# current dateTime
now = datetime.now()

# convert to string
RUNTIME_STR = now.strftime("%Y-%m-%d %H:%M:%S")

env_file_path = Path(".env")

ACTIVITY_LOG = f"{SCRIPT_NAME}.log"

setup_logger('activity_log', ACTIVITY_LOG)

plogger(f"Starting {SCRIPT_NAME} {VERSION} at {RUNTIME_STR}", 'info', 'a')

if load_and_upgrade_env(env_file_path) < 0:
    sys.exit()

PLEX_OWNER = os.getenv("TARGET_PLEX_OWNER")

LIBRARY_MAP = os.getenv("LIBRARY_MAP", "{}")

try:
    lib_map = json.loads(LIBRARY_MAP)
except: # pylint: disable=bare-except
    plogger("LIBRARY_MAP in the .env file appears to be broken.  Defaulting to an empty list.", 'info', 'a')
    lib_map = json.loads("{}")

def progress(counter, total, status=""):
    """ Display a progress bar """
    bar_len = 40
    filled_len = int(round(bar_len * counter / float(total)))

    percents = round(100.0 * counter / float(total), 1)
    p_bar = "=" * filled_len + "-" * (bar_len - filled_len)
    stat_str = textwrap.shorten(status, width=80)

    sys.stdout.write(f"[{p_bar}] {percents}% ... {stat_str.ljust(80)}\r")
    sys.stdout.flush()

def get_user_acct(acct_list, title): # pylint: disable=inconsistent-return-statements
    """ Find a user account by title """
    for acct in acct_list:
        if acct.title == title:
            return acct

PADWIDTH = 105
COUNT = 0
CONNECTED_PLEX_USER = PLEX_OWNER
CONNECTED_PLEX_LIBRARY = None
CURRENT_SHOW = None
LAST_LIBRARY = None

PLEX = get_plex()
PMI = PLEX.machineIdentifier

account = PLEX.myPlexAccount()
all_users = account.users()
ITEM = None

with open("status.txt") as fp: # pylint: disable=unspecified-encoding
    for line in fp:
        ITEM = None
        ITEMS = None

        COUNT += 1

        parts = line.split("\t")
        if len(parts) == 1:
            continue  # this is an error line

        #  chazlarson	show	TV Shows - 4K	After Life	s01e01	Episode 1
        #  0            1       2               3           4       5
        #  chazlarson	movie	Movies - 4K	10 Things I Hate About You	1999	PG-13
        #  0            1       2           3                           4       5
        plex_user = parts[0].strip()
        plex_type = parts[1].strip()
        plex_library = parts[2].strip()
        MAPPED_FROM = ""

        if plex_library in lib_map:
            MAPPED_FROM = f" [mapped from {plex_library}]"
            plex_library = lib_map[plex_library]

        if plex_type == "show":
            #  chazlarson	show	TV Shows - 4K	After Life	s01e01	Episode 1
            #  0            1       2               3           4       5
            plex_series = parts[3].strip()
            plex_ep = parts[4].strip()
            plex_title = parts[5].strip()

            tmp = re.split("[se]", plex_ep)
            # ['', '01', '14']
            try:
                plex_season = int(tmp[1])
                plex_episode = int(tmp[2])
            except: # pylint: disable=bare-except
                continue
        else:
            #  chazlarson	movie	Movies - 4K	10 Things I Hate About You	1999	PG-13
            #  0            1       2           3                           4       5
            plex_title = parts[3].strip()  # Episode 2
            plex_year = parts[4].strip()
            plex_rating = parts[5].strip()

        if plex_user != CONNECTED_PLEX_USER:
            PLEX = None
            if plex_user.lower() == PLEX_OWNER.lower():
                PLEX = get_plex()
            else:
                user_acct = get_user_acct(all_users, plex_user)
                if user_acct:
                    PLEX = get_plex(user_acct.get_token(PMI))
            if PLEX is not None:
                CONNECTED_PLEX_USER = plex_user
                print(f"------------ {CONNECTED_PLEX_USER} ------------")
            else:
                CONNECTED_PLEX_USER = None
                print(f"---- NOT FOUND: {plex_user} ------------")


        if PLEX is not None:
            if plex_library != CONNECTED_PLEX_LIBRARY:
                try:
                    ITEMS = PLEX.library.section(plex_library)
                    CONNECTED_PLEX_LIBRARY = plex_library
                    LAST_LIBRARY = None
                    print(
                        f"\r{os.linesep}------------ {CONNECTED_PLEX_LIBRARY}{MAPPED_FROM} ------------"
                    )
                except: # pylint: disable=bare-except
                    if LAST_LIBRARY is None:
                        print(
                            f"\r{os.linesep}------------ Exception connecting to {plex_library} ------------"
                        )
                        LAST_LIBRARY = plex_library
                    CONNECTED_PLEX_LIBRARY = None
            else:
                CONNECTED_PLEX_LIBRARY = None

        if CONNECTED_PLEX_LIBRARY is not None:

            if plex_type == "show":
                PLEX_TARGET = f"{plex_series} {plex_ep}"
                sys.stdout.write(
                    f"\rSearching for unwatched {plex_series}".ljust(PADWIDTH)
                )
                sys.stdout.flush()
                CORRECT_SHOW = None
                UNWATCHED_EPS = None
                THINGS = None
                if CURRENT_SHOW != plex_series:
                    THINGS = ITEMS.searchShows(title=plex_series, unwatched=True)
                    CURRENT_SHOW = plex_series
                if len(THINGS) > 0:
                    TITLE_CT = 0
                    if CORRECT_SHOW is None:
                        for thing in THINGS:
                            if ITEM is None:
                                TITLE_CT += 1
                                if thing.title == plex_series:
                                    CORRECT_SHOW = thing
                    if CORRECT_SHOW is not None:
                        if UNWATCHED_EPS is None:
                            UNWATCHED_EPS = CORRECT_SHOW.unwatched()

                        for epi in UNWATCHED_EPS:
                            if epi.seasonEpisode == plex_ep:
                                ITEM = epi
                else:
                    sys.stdout.write(
                        f"\rSkipping {PLEX_TARGET} - show is watched".ljust(PADWIDTH)
                    )
                    sys.stdout.flush()
            elif plex_type == "movie":
                PLEX_TARGET = f"{plex_title} ({plex_year})"
                sys.stdout.write(
                    f"\rSearching for an unwatched {PLEX_TARGET}".ljust(PADWIDTH)
                )
                sys.stdout.flush()
                THINGS = ITEMS.search(title=plex_title, unwatched=True)
                TITLE_CT = 0
                TITLE_MATCH_CT = 0
                TITLE_YEAR_CT = 0
                TITLE_RATING_CT = 0
                for thing in THINGS:
                    if ITEM is None:
                        TITLE_CT += 1
                        unWatched = not thing.isPlayed
                        if thing.title == plex_title:
                            TITLE_MATCH_CT += 1
                            if thing.year == int(plex_year):
                                TITLE_YEAR_CT += 1
                                if thing.contentRating == plex_rating:
                                    TITLE_RATING_CT += 1
                                    if unWatched:
                                        ITEM = thing

                if TITLE_MATCH_CT > 1:
                    print(
                        f"\r{TITLE_MATCH_CT} title matches for {plex_title}".ljust(
                            PADWIDTH
                        )
                    )
                if TITLE_YEAR_CT > 1:
                    print(
                        f"\r{TITLE_YEAR_CT} title-year matches for {plex_title}".ljust(
                            PADWIDTH
                        )
                    )
                if TITLE_RATING_CT > 1:
                    print(
                        f"\r{TITLE_RATING_CT} title-year-rating matches for {plex_title}".ljust(
                            PADWIDTH
                        )
                    )
            else:
                print(f"Unknown type: {plex_type}")

            if ITEM is not None:
                # print(f"\rPicked {ITEM.title} - {ITEM.year} - {ITEM.contentRating} for {plex_title}".ljust(PADWIDTH))
                if not ITEM.isPlayed:
                    print(
                        f"\rMarked watched for {CONNECTED_PLEX_USER} - {PLEX_TARGET}".ljust(
                            PADWIDTH
                        )
                    )
                    ITEM.markPlayed()
                # else:
                #     print(f"\rAlready marked watched for {CONNECTED_PLEX_USER}")
            # sys.stdout.write(f"\r ".ljust(PADWIDTH))
            # sys.stdout.flush()
