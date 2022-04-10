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
from pathvalidate import is_valid_filename, sanitize_filename

load_dotenv()

PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')
LIBRARY_NAME = os.getenv('LIBRARY_NAME')
LIBRARY_NAMES = os.getenv('LIBRARY_NAMES')
POSTER_DIR = os.getenv('CURRENT_POSTER_DIR')
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


def validate_filename(filename):
    if is_valid_filename(filename):
        return filename, None
    else:
        mapping_name = sanitize_filename(filename)
        return mapping_name, f"Log Folder Name: {filename} is invalid using {mapping_name}"

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
        dir_name, msg = validate_filename(item.title)
        attempts = 0

        progress_str = f"{item.title}"

        progress(item_count, item_total, progress_str)

        while attempts < 5:
            try:

                progress_str = f"{item.title} - {attempts}"

                progress(item_count, item_total, progress_str)

                # item.art
                # '/library/metadata/2273137/art/1646196834'

                # print(poster)
                artwork_path = Path(tgt_dir, f"{dir_name}")
                tgt_file_path = f"{item.ratingKey}.png"
                final_file_path = f"{artwork_path}/{tgt_file_path}"

                src_URL = item.art
                if src_URL[0] == '/':
                    src_URL = f"{PLEX_URL}{item.art}&X-Plex-Token={PLEX_TOKEN}"

                if not os.path.exists(final_file_path):
                    if POSTER_DOWNLOAD:
                        p = Path(artwork_path)
                        p.mkdir(parents=True, exist_ok=True)

                        thumbPath = download(f"{src_URL}", PLEX_TOKEN, filename=tgt_file_path, savepath=artwork_path)
                    else:
                        script_line = f"mkdir -p \"{dir_name}\" && curl -C - -fLo \"{dir_name}/{tgt_file_path}\" {src_URL}"
                        script_string = script_string + f"{script_line}\n"
                attempts = 6

            except Exception as ex:
                progress(item_count, item_total, "EX: " + item.title)
                attempts += 1

    print("\n")
    if len(script_string) > 0:
        with open(f"{tgt_dir}/get_images.sh", 'w') as myfile:
            myfile.write(f"{script_string}\n")
