import logging
from plexapi.server import PlexServer
from plexapi.exceptions import Unauthorized
import os
import imdb
from dotenv import load_dotenv
import sys
import textwrap
from helpers import booler, get_ids

SCRIPT_NAME = "grab-imdb-posters"
logging.basicConfig(
    filename=f"{SCRIPT_NAME}.log",
    filemode="w",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logging.info(f"Starting {SCRIPT_NAME}.py")

if os.path.exists(".env"):
    load_dotenv()
else:
    logging.info(f"No environment [.env] file.  Exiting.")
    print(f"No environment [.env] file.  Exiting.")
    exit()

PLEX_URL = os.getenv("PLEX_URL")
PLEX_TOKEN = os.getenv("PLEX_TOKEN")
TMDB_KEY = os.getenv("TMDB_KEY")
LIBRARY_NAME = os.getenv("LIBRARY_NAME")
LIBRARY_NAMES = os.getenv("LIBRARY_NAMES")
POSTER_DIR = os.getenv("POSTER_DIR")
POSTER_DEPTH = int(os.getenv("POSTER_DEPTH"))
POSTER_DOWNLOAD = booler(os.getenv("POSTER_DOWNLOAD"))
POSTER_CONSOLIDATE = booler(os.getenv("POSTER_CONSOLIDATE"))

if POSTER_DEPTH is None:
    POSTER_DEPTH = 0

if POSTER_DOWNLOAD:
    script_string = f'#!/bin/bash{os.linesep}{os.linesep}# SCRIPT TO DO STUFF{os.linesep}{os.linesep}cd "{POSTER_DIR}"{os.linesep}{os.linesep}'
else:
    script_string = ""

if LIBRARY_NAMES:
    lib_array = LIBRARY_NAMES.split(",")
else:
    lib_array = [LIBRARY_NAME]

imdb_str = "imdb://"
tmdb_str = "tmdb://"
tvdb_str = "tvdb://"

def progress(count, total, status=""):
    bar_len = 40
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = "=" * filled_len + "-" * (bar_len - filled_len)
    stat_str = textwrap.shorten(status, width=80)

    sys.stdout.write("[%s] %s%s ... %s\r" % (bar, percents, "%", stat_str.ljust(80)))
    sys.stdout.flush()

all_items = []

print(f"connecting to {PLEX_URL}...")
logging.info(f"connecting to {PLEX_URL}...")
try:
    plex = PlexServer(PLEX_URL, PLEX_TOKEN)
except Unauthorized:
    print("Plex Error: Plex token is invalid")
    exit()
except Exception as ex:
  print(f"Plex Error: {ex.args}")
  exit()

logging.info("connection success")

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
        imdb_id, tmdb_id, tvdb_id = get_ids(item.guids, TMDB_KEY)

        tmpDict = {}
        tmpDict["title"] = item.title
        tmpDict["ratingKey"] = item.ratingKey
        tmpDict["imdb"] = imdb_id
        tmpDict["tmdb"] = tmdb_id
        tmpDict["tvdb"] = tvdb_id
        all_items.append(tmpDict)

        progress_str = f"{item.title}"
        progress(item_count, item_total, progress_str)

    print("{os.linesep}")

print("processing items...")
item_total = len(all_items)
print(f"looping over {item_total} items...")
item_count = 0

# creating instance of IMDb
ia = imdb.IMDb()

for item in all_items:
    item_count = item_count + 1

    progress_str = f"{item['title']}"
    progress(item_count, item_total, progress_str)

    # id
    code = "6468322"
    imdid = item["imdb"].replace("tt", "")

    # getting information
    series = ia.get_movie(imdid)

    # getting cover url of the series
    cover = series.data["cover url"]
