from xmlrpc.client import Boolean
from plexapi.server import PlexServer
from plexapi.utils import download
import os
import imdb
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
POSTER_DIR = os.getenv('POSTER_DIR')
POSTER_DEPTH =  int(os.getenv('POSTER_DEPTH'))
POSTER_DOWNLOAD =  Boolean(int(os.getenv('POSTER_DOWNLOAD')))
POSTER_CONSOLIDATE =  Boolean(int(os.getenv('POSTER_CONSOLIDATE')))

if POSTER_DEPTH is None:
    POSTER_DEPTH = 0

if POSTER_DOWNLOAD:
    script_string = f"#!/bin/bash\n\n# SCRIPT TO DO STUFF\n\ncd \"{POSTER_DIR}\"\n\n"
else:
    script_string = ""

if LIBRARY_NAMES:
    lib_array = LIBRARY_NAMES.split(",")
else:
    lib_array = [LIBRARY_NAME]

imdb_str = 'imdb://'
tmdb_str = 'tmdb://'
tvdb_str = 'tvdb://'

def getTID(theList):
    imdbid = None
    tmid = None
    tvid = None
    for guid in theList:
        if imdb_str in guid.id:
            imdbid = guid.id.replace(imdb_str,'')
        if tmdb_str in guid.id:
            tmid = guid.id.replace(tmdb_str,'')
        if tvdb_str in guid.id:
            tvid = guid.id.replace(tvdb_str,'')
    return imdbid, tmid, tvid

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

all_items = []

print(f"connecting to {PLEX_URL}...")
plex = PlexServer(PLEX_URL, PLEX_TOKEN)
for lib in lib_array:
    print(f"getting items from [{lib}]...")
    items = plex.library.section(lib).all()
    item_total = len(items)
    print(f"looping over {item_total} items...")
    item_count = 0

    plex_links = []
    external_links = []

    for item in items:
        item_count = item_count + 1
        imdb_id, tmdb_id, tvdb_id = getTID(item.guids)

        tmpDict = {}
        tmpDict["title"] = item.title
        tmpDict["ratingKey"] = item.ratingKey
        tmpDict["imdb"] = imdb_id
        tmpDict["tmdb"] = tmdb_id
        tmpDict["tvdb"] = tvdb_id
        all_items.append(tmpDict)

        progress_str = f"{item.title}"
        progress(item_count, item_total, progress_str)

    print("\n")

print(f"processing items...")
item_total = len(all_items)
print(f"looping over {item_total} items...")
item_count = 0

# creating instance of IMDb
ia = imdb.IMDb()

for item in all_items:
    item_count = item_count + 1

    progress_str = f"{item.title}"
    progress(item_count, item_total, progress_str)

    # id
    code = "6468322"
    imdid = item.imdb.replace('tt','')

    # getting information
    series = ia.get_movie(code)

    # getting cover url of the series
    cover = series.data['cover url']
