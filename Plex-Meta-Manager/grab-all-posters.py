from xmlrpc.client import Boolean
from plexapi.server import PlexServer
from plexapi.utils import download
import os
from dotenv import load_dotenv
import sys
import textwrap
from tmdbapis import TMDbAPIs
import requests
from pathlib import Path, PurePath

load_dotenv()

PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')
LIBRARY_NAME = os.getenv('LIBRARY_NAME')
LIBRARY_NAMES = os.getenv('LIBRARY_NAMES')
POSTER_DIR = os.getenv('POSTER_DIR')
POSTER_DEPTH =  int(os.getenv('POSTER_DEPTH'))
POSTER_DOWNLOAD =  Boolean(int(os.getenv('POSTER_DOWNLOAD')))

if POSTER_DEPTH is None:
    POSTER_DEPTH = 0

if LIBRARY_NAMES:
    lib_array = LIBRARY_NAMES.split(",")
else:
    lib_array = [LIBRARY_NAME]

def progress(count, total, status=''):
    bar_len = 40
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)
    stat_str = textwrap.shorten(status, width=80)

    sys.stdout.write('[%s] %s%s ... %s\r' % (bar, percents, '%', stat_str.ljust(80)))
    sys.stdout.flush()


print(f"connecting to {PLEX_URL}...")
plex = PlexServer(PLEX_URL, PLEX_TOKEN)
for lib in lib_array:
    print(f"getting items from [{lib}]...")
    items = plex.library.section(lib).all()
    item_total = len(items)
    print(f"looping over {item_total} items...")
    item_count = 1

    plex_links = []
    external_links = []
    script_string = f"#!/bin/bash\n\n# SCRIPT TO DO STUFF\n\ncd \"{POSTER_DIR}\"\n\n"

    for item in items:
        tmpDict = {}
        item_count = item_count + 1
        tgt_dir = f"{POSTER_DIR}/{lib}"

        attempts = 0

        while attempts < 5:
            try:

                posters = item.posters()
                progress_str = f"{item.title} - {len(posters)} posters"

                progress(item_count, item_total, progress_str)

                idx = 1
                for poster in posters:
                    if POSTER_DEPTH > 0 and idx > POSTER_DEPTH:
                        break

                    poster_obj = {}
                    # print(poster)
                    dir_name = item.title
                    artwork_path = Path(tgt_dir, f"{dir_name}")
                    tgt_file_path = f"{item.ratingKey}-{str(idx).zfill(3)}.png"
                    final_file_path = f"{artwork_path}/{tgt_file_path}"

                    poster_obj["folder"] = artwork_path
                    poster_obj["file"] = tgt_file_path

                    src_URL = poster.key
                    if src_URL[0] == '/':
                        src_URL = f"{PLEX_URL}{poster.key}&X-Plex-Token={PLEX_TOKEN}"
                        poster_obj["URL"] = src_URL
                        # plex_links.append(poster_obj)
                    else:
                        poster_obj["URL"] = src_URL
                        # external_links.append(poster_obj)

                    progress(item_count, item_total, f"{progress_str} - {idx}")

                    if not os.path.exists(final_file_path):
                        if POSTER_DOWNLOAD:
                            p = Path(artwork_path)
                            p.mkdir(parents=True, exist_ok=True)

                            thumbPath = download(f"{src_URL}", PLEX_TOKEN, filename=tgt_file_path, savepath=artwork_path)
                        else:
                            script_line = f"mkdir -p \"{dir_name}\" && curl -C - -fLo \"{dir_name}/{tgt_file_path}\" {src_URL}"
                            script_string = script_string + f"{script_line}\n"

                    idx += 1
                attempts = 6
            except Exception as ex:
                progress(item_count, item_total, "EX: " + item.title)
                attempts += 1

    print("\n")
    if len(script_string) > 0:
        with open(f"{tgt_dir}/get_images.sh", 'w') as myfile:
            myfile.write(f"{script_string}\n")
