""" reverse the genres on all movies or shows in a library """
#!/usr/bin/env python
import os
import sys

from pathlib import Path
from datetime import datetime

from helpers import get_all_from_library, get_plex, load_and_upgrade_env

from logs import setup_logger, plogger, logger

from alive_progress import alive_bar

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
    sys.exit()

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

def reverse_genres(tgt_item):
    """ reverse the genres on a movie or show """
    reversed_list = []

    tgt_item.reload()
    genres = tgt_item.genres

    print(f"{tgt_item.title} before: {genres}")

    tgt_item.removeGenre(genres)

    for genre in genres:
        reversed_list.insert(0, genre)

    print(f"{tgt_item.title} reversed: {reversed_list}")

    for genre in reversed_list:
        print(f"{tgt_item.title} adding: {genre}")
        tgt_item.addGenre(genre)
        tgt_item.reload()

    tgt_item.reload()
    new_genres = tgt_item.genres

    print(f"{tgt_item.title} after: {new_genres}")


if LIBRARY_NAMES == 'ALL_LIBRARIES':
    LIB_ARRAY = []
    all_libs = plex.library.sections()
    for lib in all_libs:
        if lib.type in ('movie', 'show'):
            LIB_ARRAY.append(lib.title.strip())

for lib in LIB_ARRAY:

    try:
        the_lib = plex.library.section(lib)

        count = plex.library.section(lib).totalSize
        print(f"getting {count} {the_lib.type}s from [{lib}]...")
        logger((f"getting {count} {the_lib.type}s from [{lib}]..."), 'info', 'a')
        item_total, items = get_all_from_library(the_lib)
        logger((f"looping over {item_total} items..."), 'info', 'a')
        ITEM_COUNT = 1

        plex_links = []
        external_links = []

        with alive_bar(item_total, dual_line=True, title="Reverse Genres") as bar:
            for item in items:
                logger(("================================"), 'info', 'a')
                logger((f"Starting {item.title}"), 'info', 'a')

                reverse_genres(item)

                bar() # pylint: disable=not-callable

        logger(("COMPLETE"), 'info', 'a')
        bar.text = "COMPLETE"

        print(os.linesep)

    except Exception as ex: # pylint: disable=broad-exception-caught
        logger((f"Problem processing {lib}; {ex}"), 'info', 'a')
        print(f"Problem processing {lib}; {ex}")
