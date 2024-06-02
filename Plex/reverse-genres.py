#!/usr/bin/env python
import logging
import os
from multiprocessing import cpu_count
from multiprocessing.pool import ThreadPool

import piexif.helper
from alive_progress import alive_bar
from dotenv import load_dotenv

from helpers import booler, get_all_from_library, get_plex, load_and_upgrade_env

from logs import setup_logger, plogger, blogger, logger

from pathlib import Path
from datetime import datetime, timedelta
# current dateTime
now = datetime.now()

# convert to string
RUNTIME_STR = now.strftime("%Y-%m-%d %H:%M:%S")

SCRIPT_NAME = Path(__file__).stem

VERSION = "0.1.0"

env_file_path = Path(".env")

ACTIVITY_LOG = f"{SCRIPT_NAME}.log"
setup_logger('activity_log', ACTIVITY_LOG)

plogger(f"Starting {SCRIPT_NAME} {VERSION} at {RUNTIME_STR}", 'info', 'a')

if load_and_upgrade_env(env_file_path) < 0:
    exit()

LIBRARY_NAME = os.getenv("LIBRARY_NAME")
LIBRARY_NAMES = os.getenv("LIBRARY_NAMES")
NEW = []
UPDATED = []

if LIBRARY_NAMES:
    LIB_ARRAY = [s.strip() for s in LIBRARY_NAMES.split(",")]
else:
    LIB_ARRAY = [LIBRARY_NAME]

plex = get_plex()

logger(("connection success"), 'info', 'a')

def reverse_genres(item):
    reversed_list = []

    item.reload()
    genres = item.genres

    print(f"{item.title} before: {genres}")

    item.removeGenre(genres)

    for genre in genres:
        reversed_list.insert(0, genre)
    
    print(f"{item.title} reversed: {reversed_list}")

    for genre in reversed_list:
        print(f"{item.title} adding: {genre}")
        item.addGenre(genre)
        item.reload()

    item.reload()
    new_genres = item.genres

    print(f"{item.title} after: {new_genres}")


if LIBRARY_NAMES == 'ALL_LIBRARIES':
    LIB_ARRAY = []
    all_libs = plex.library.sections()
    for lib in all_libs:
        if lib.type == 'movie' or lib.type == 'show':
            LIB_ARRAY.append(lib.title.strip())

for lib in LIB_ARRAY:

    try:
        the_lib = plex.library.section(lib)

        count = plex.library.section(lib).totalSize
        print(f"getting {count} {the_lib.type}s from [{lib}]...")
        logger((f"getting {count} {the_lib.type}s from [{lib}]..."), 'info', 'a')
        item_total, items = get_all_from_library(the_lib)
        logger((f"looping over {item_total} items..."), 'info', 'a')
        item_count = 1

        plex_links = []
        external_links = []

        with alive_bar(item_total, dual_line=True, title="Reverse Genres") as bar:
            for item in items:
                logger(("================================"), 'info', 'a')
                logger((f"Starting {item.title}"), 'info', 'a')

                reverse_genres(item)

                bar()

        progress_str = "COMPLETE"
        logger((progress_str), 'info', 'a')

        bar.text = progress_str

        print(os.linesep)

    except Exception as ex:
        progress_str = f"Problem processing {lib}; {ex}"
        logger((progress_str), 'info', 'a')

        print(progress_str)
