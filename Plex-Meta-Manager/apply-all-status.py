from xmlrpc.client import Boolean
from plexapi.server import PlexServer
from plexapi.utils import download
import os
from dotenv import load_dotenv
import re
import sys
import textwrap
import requests
from pathlib import Path, PurePath
from pathvalidate import is_valid_filename, sanitize_filename

load_dotenv()

PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')
PLEX_OWNER = os.getenv('PLEX_OWNER')

def progress(count, total, status=''):
    bar_len = 40
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)
    stat_str = textwrap.shorten(status, width=80)

    sys.stdout.write('[%s] %s%s ... %s\r' % (bar, percents, '%', stat_str.ljust(80)))
    sys.stdout.flush()


def validate_filename(filename):
    if is_valid_filename(filename):
        return filename, None
    else:
        mapping_name = sanitize_filename(filename)
        return mapping_name, f"Log Folder Name: {filename} is invalid using {mapping_name}"

def get_user_acct(acct_list, username):
    for acct in acct_list:
        if acct.username == username:
            return acct

padwidth = 95
count = 0
connected_plex_user = PLEX_OWNER
connected_plex_library = ""

print(f"connecting to {PLEX_URL}...")
plex = PlexServer(PLEX_URL, PLEX_TOKEN)
PMI = plex.machineIdentifier

account = plex.myPlexAccount()
all_users = account.users()
item = None

with open(f"status.txt") as fp:
    for line in fp:

        count += 1

        parts = line.split('\t')
        if len(parts) == 1:
            continue # this is an error line

        plex_user = parts[0].strip()
        plex_type = parts[1].strip()
        plex_library = parts[2].strip()
        plex_title = parts[3].strip()
        if len(parts) > 4 and plex_type == "show":
            plex_series = parts[4].strip()
            plex_ep = parts[5].strip()
            tmp = re.split('[se]', plex_ep)
            # ['', '01', '14']
            try:
                plex_season = int(tmp[1])
                plex_episode = int(tmp[2])
            except:
                continue
        else:
            plex_year = parts[4].strip()
            plex_rating = parts[5].strip()

        if plex_user != connected_plex_user:
            if plex_user == PLEX_OWNER:
                plex = PlexServer(PLEX_URL, PLEX_TOKEN)
            else:
                user_acct = get_user_acct(all_users, plex_user)
                plex = PlexServer(PLEX_URL, user_acct.get_token(PMI))
            connected_plex_user = plex_user
            print(f"------------ {connected_plex_user} ------------")

        if plex_library != connected_plex_library:
            items = plex.library.section(plex_library)
            connected_plex_library = plex_library
            print(f"\r\n------------ {connected_plex_library} ------------")

        things = None
        thing = None
        item = None

        if plex_type == 'show':
            sys.stdout.write(f"\rSearching for {plex_series} {plex_ep} {plex_title}".ljust(padwidth))
            sys.stdout.flush()
            things = items.searchShows(title=plex_series)
            title_ct = 0
            for thing in things:
                if item is None:
                    title_ct += 1
                    if thing.title == plex_series:
                        try:
                            item = thing.episode(season=plex_season, episode=plex_episode)
                            sys.stdout.write(f"\rSearching for {plex_series} {plex_ep} {plex_title}: found in {title_ct} - {thing.title}".ljust(padwidth))
                            sys.stdout.flush()
                        except:
                            sys.stdout.write(f"\rSearching for {plex_series} {plex_ep} {plex_title}: NOT found in {title_ct} - {thing.title}".ljust(padwidth))
                            sys.stdout.flush()
        elif plex_type == 'movie':
            sys.stdout.write(f"\rSearching for {plex_title}".ljust(padwidth))
            sys.stdout.flush()
            things = items.search(title=plex_title, unwatched=True)
            title_ct = 0
            title_match_ct = 0
            title_year_ct = 0
            title_rating_ct = 0
            for thing in things:
                if item is None:
                    title_ct += 1
                    unWatched = not thing.isWatched;
                    # sys.stdout.write(f"\rSearching for {plex_title}: {title_ct} - {thing.title} ({thing.year}) ".ljust(padwidth))
                    # sys.stdout.flush()
                    if thing.title == plex_title:
                        title_match_ct += 1
                        if thing.year == int(plex_year):
                            title_year_ct += 1
                            if thing.contentRating == plex_rating:
                                title_rating_ct += 1
                                if unWatched:
                                    item = thing

            if title_match_ct > 1:
                print(f"\r{title_match_ct} matches for {plex_title}")
            if title_year_ct > 1:
                print(f"\r{title_year_ct} matches for {plex_title}")
            if title_rating_ct > 1:
                print(f"\r{title_rating_ct} matches for {plex_title}")
        else:
            print(f"Unknown type: {plex_type}")

        if item is not None:
            if not item.isWatched:
                print(f"Marked watched for {connected_plex_user}")
                item.markWatched()
            else:
                print(f"Already marked watched for {connected_plex_user}")
