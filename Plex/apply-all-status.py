import json
import os
import re
import sys
import textwrap
from dotenv import load_dotenv
from plexapi.server import PlexServer
from helpers import get_all, get_plex

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

PLEX_URL = os.getenv("TARGET_PLEX_URL")
PLEX_TOKEN = os.getenv("TARGET_PLEX_TOKEN")
PLEX_OWNER = os.getenv("TARGET_PLEX_OWNER")

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


def get_user_acct(acct_list, title):
    for acct in acct_list:
        if acct.title == title:
            return acct


padwidth = 105
count = 0
connected_plex_user = PLEX_OWNER
connected_plex_library = None
current_show = None
last_library = None

plex = get_plex(PLEX_URL, PLEX_TOKEN)
PMI = plex.machineIdentifier

account = plex.myPlexAccount()
all_users = account.users()
item = None

with open("status.txt") as fp:
    for line in fp:
        item = None

        count += 1

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
        mapped_from = ""

        if plex_library in lib_map:
            mapped_from = f" [mapped from {plex_library}]"
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
            except:
                continue
        else:
            #  chazlarson	movie	Movies - 4K	10 Things I Hate About You	1999	PG-13
            #  0            1       2           3                           4       5
            plex_title = parts[3].strip()  # Episode 2
            plex_year = parts[4].strip()
            plex_rating = parts[5].strip()

        if plex_user != connected_plex_user:
            if plex_user.lower() == PLEX_OWNER.lower():
                plex = get_plex(PLEX_URL, PLEX_TOKEN)
            else:
                user_acct = get_user_acct(all_users, plex_user)
                plex = get_plex(PLEX_URL, user_acct.get_token(PMI))
            connected_plex_user = plex_user
            print(f"------------ {connected_plex_user} ------------")

        if plex_library != connected_plex_library:
            try:
                items = plex.library.section(plex_library)
                connected_plex_library = plex_library
                last_library = None
                print(
                    f"\r{os.linesep}------------ {connected_plex_library}{mapped_from} ------------"
                )
            except:
                if last_library is None:
                    print(
                        f"\r{os.linesep}------------ Exception connecting to {plex_library} ------------"
                    )
                    last_library = plex_library
                connected_plex_library = None

        if connected_plex_library is not None:

            if plex_type == "show":
                plex_target = f"{plex_series} {plex_ep}"
                sys.stdout.write(
                    f"\rSearching for unwatched {plex_series}".ljust(padwidth)
                )
                sys.stdout.flush()
                if current_show != plex_series:
                    things = items.searchShows(title=plex_series, unwatched=True)
                    current_show = plex_series
                    correct_show = None
                    unwatched_eps = None
                if len(things) > 0:
                    title_ct = 0
                    if correct_show is None:
                        for thing in things:
                            if item is None:
                                title_ct += 1
                                if thing.title == plex_series:
                                    correct_show = thing
                    if correct_show is not None:
                        if unwatched_eps is None:
                            unwatched_eps = correct_show.unwatched()

                        for epi in unwatched_eps:
                            if epi.seasonEpisode == plex_ep:
                                item = epi
                else:
                    sys.stdout.write(
                        f"\rSkipping {plex_target} - show is watched".ljust(padwidth)
                    )
                    sys.stdout.flush()
            elif plex_type == "movie":
                plex_target = f"{plex_title} ({plex_year})"
                sys.stdout.write(
                    f"\rSearching for an unwatched {plex_target}".ljust(padwidth)
                )
                sys.stdout.flush()
                things = items.search(title=plex_title, unwatched=True)
                title_ct = 0
                title_match_ct = 0
                title_year_ct = 0
                title_rating_ct = 0
                for thing in things:
                    if item is None:
                        title_ct += 1
                        unWatched = not thing.isPlayed
                        if thing.title == plex_title:
                            title_match_ct += 1
                            if thing.year == int(plex_year):
                                title_year_ct += 1
                                if thing.contentRating == plex_rating:
                                    title_rating_ct += 1
                                    if unWatched:
                                        item = thing

                if title_match_ct > 1:
                    print(
                        f"\r{title_match_ct} title matches for {plex_title}".ljust(
                            padwidth
                        )
                    )
                if title_year_ct > 1:
                    print(
                        f"\r{title_year_ct} title-year matches for {plex_title}".ljust(
                            padwidth
                        )
                    )
                if title_rating_ct > 1:
                    print(
                        f"\r{title_rating_ct} title-year-rating matches for {plex_title}".ljust(
                            padwidth
                        )
                    )
            else:
                print(f"Unknown type: {plex_type}")

            if item is not None:
                # print(f"\rPicked {item.title} - {item.year} - {item.contentRating} for {plex_title}".ljust(padwidth))
                if not item.isPlayed:
                    print(
                        f"\rMarked watched for {connected_plex_user} - {plex_target}".ljust(
                            padwidth
                        )
                    )
                    item.markPlayed()
                # else:
                #     print(f"\rAlready marked watched for {connected_plex_user}")
            # sys.stdout.write(f"\r ".ljust(padwidth))
            # sys.stdout.flush()
