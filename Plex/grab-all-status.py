from plexapi.server import PlexServer
import os
import json
from dotenv import load_dotenv

import sys
import textwrap

load_dotenv()

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
    print(file_line)
    return file_line


def process_section(ps, user):
    plex_sections = ps.library.sections()
    for plex_section in plex_sections:
        if plex_section.type != "artist":
            print(f"------------ {plex_section.title} ------------")
            items = plex.library.section(plex_section.title)
            if items.type == "show":
                print("Gathering watched episodes...")
                for video in items.searchEpisodes(unwatched=False):
                    file_string = (
                        file_string
                        + get_data_line(
                            account.username, items.type, plex_section.title, video
                        )
                        + f"{os.linesep}"
                    )
            elif items.type == "movie":
                print("Gathering watched movies...")
                for video in items.search(unwatched=False):
                    file_string = (
                        file_string
                        + get_data_line(
                            account.username, items.type, plex_section.title, video
                        )
                        + f"{os.linesep}"
                    )
            else:
                file_line = f"Unknown type: {items.type}"
                print(file_line)
                file_string = file_string + f"{file_line}{os.linesep}"
        else:
            file_line = f"Skipping {plex_section.title}"
            print(file_line)
            file_string = file_string + f"{file_line}{os.linesep}"
    return False


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
        if plex_section.type != "artist":
            print(f"------------ {plex_section.title} ------------")
            items = plex.library.section(plex_section.title)
            if items.type == "show":
                print("Gathering watched episodes...")
                for video in items.searchEpisodes(unwatched=False):
                    file_string = (
                        file_string
                        + get_data_line(
                            account.username, items.type, plex_section.title, video
                        )
                        + f"{os.linesep}"
                    )
            elif items.type == "movie":
                print("Gathering watched movies...")
                for video in items.search(unwatched=False):
                    file_string = (
                        file_string
                        + get_data_line(
                            account.username, items.type, plex_section.title, video
                        )
                        + f"{os.linesep}"
                    )
            else:
                file_line = f"Unknown type: {items.type}"
                print(file_line)
                file_string = file_string + f"{file_line}{os.linesep}"
        else:
            file_line = f"Skipping {plex_section.title}"
            print(file_line)
            file_string = file_string + f"{file_line}{os.linesep}"
except:
    file_line = f"Exception processing {account.username}"
    print(file_line)
    file_string = file_string + f"{file_line}{os.linesep}"

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
            if plex_section.type != "artist":
                print(f"------------ {plex_section.title} ------------")
                items = user_plex.library.section(plex_section.title)
                if items.type == "show":
                    for video in items.searchEpisodes(unwatched=False):
                        file_string = (
                            file_string
                            + get_data_line(
                                plex_user.username,
                                items.type,
                                plex_section.title,
                                video,
                            )
                            + f"{os.linesep}"
                        )
                elif items.type == "movie":
                    for video in items.search(unwatched=False):
                        file_string = (
                            file_string
                            + get_data_line(
                                plex_user.username,
                                items.type,
                                plex_section.title,
                                video,
                            )
                            + f"{os.linesep}"
                        )
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
    with open("status.txt", "w", encoding="utf-8") as myfile:
        myfile.write(f"{file_string}{os.linesep}")
