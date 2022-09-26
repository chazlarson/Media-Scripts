from xmlrpc.client import Boolean
from plexapi.server import PlexServer
from plexapi.utils import download
import os
from dotenv import load_dotenv

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
file_string = ""

print(f"------------ {account.username} ------------")
try:
    plex_sections = plex.library.sections()
    for plex_section in plex_sections:
        if plex_section.type != 'artist':
            print(f"------------ {plex_section.title} ------------")
            items = plex.library.section(plex_section.title)
            if items.type == 'show':
                for video in items.searchEpisodes(unwatched=False):
                    file_line = f"{account.username}\t{items.type}\t{plex_section.title}\t{video.title}\t{video.grandparentTitle}\t{video.seasonEpisode}"
                    file_string = file_string + f"{file_line}{os.linesep}"
                    print(file_line)
            elif items.type == 'movie':
                for video in items.search(unwatched=False):
                    file_line = f"{account.username}\t{items.type}\t{plex_section.title}\t{video.title}\t{video.year}\t{video.contentRating}"
                    file_string = file_string + f"{file_line}{os.linesep}"
                    print(file_line)
            else:
                file_line = f"Unknown type: {items.type}"
                file_string = file_string + f"{file_line}{os.linesep}"
                print(file_line)
        else:
            file_line = f"Skipping {plex_section.title}"
            file_string = file_string + f"{file_line}{os.linesep}"
            print(file_line)
except:
    file_line = f"Exception processing {account.username}"
    file_string = file_string + f"{file_line}{os.linesep}"
    print(file_line)

user_ct = len(all_users)
user_idx = 0
for plex_user in all_users:
    user_acct = account.user(plex_user.username)
    user_idx += 1
    print(f"------------ {plex_user.username} {user_idx}/{user_ct} ------------")
    try:
        user_plex = PlexServer(PLEX_URL, user_acct.get_token(plex.machineIdentifier))

        plex_sections = user_plex.library.sections()
        for plex_section in plex_sections:
            if plex_section.type != 'artist':
                print(f"------------ {plex_section.title} ------------")
                items = user_plex.library.section(plex_section.title)
                if items.type == 'show':
                    for video in items.searchEpisodes(unwatched=False):
                        file_line = f"{plex_user.username}\t{items.type}\t{plex_section.title}\t{video.grandparentTitle}\t{video.seasonEpisode}\t{video.title}"
                        file_string = file_string + f"{file_line}{os.linesep}"
                        print(file_line)
                elif items.type == 'movie':
                    for video in items.search(unwatched=False):
                        file_line = f"{plex_user.username}\t{items.type}\t{plex_section.title}\t{video.title}\t{video.year}\t{video.contentRating}"
                        file_string = file_string + f"{file_line}{os.linesep}"
                        print(file_line)
                else:
                    file_line = f"Unknown type: {items.type}"
                    file_string = file_string + f"{file_line}{os.linesep}"
                    print(file_line)
            else:
                file_line = f"Skipping {plex_section.title}"
                file_string = file_string + f"{file_line}{os.linesep}"
                print(file_line)
    except:
        file_line = f"Exception processing {plex_user.username}"
        file_string = file_string + f"{file_line}{os.linesep}"
        print(file_line)

    print(f"{os.linesep}")
    if len(file_string) > 0:
        with open(f"status.txt", 'w', encoding='utf-8') as myfile:
            myfile.write(f"{file_string}{os.linesep}")

