""" Refresh metadata for all items in a library """
#!/usr/bin/env python
import os
import sys
import textwrap
import time
import logging
from pathlib import Path
from datetime import datetime

import urllib3.exceptions
from requests import ReadTimeout
from logs import setup_logger, plogger, logger
from helpers import get_plex, load_and_upgrade_env, get_all_from_library, booler
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

plex = get_plex()

LIBRARY_NAME = os.getenv("LIBRARY_NAME")
LIBRARY_NAMES = os.getenv("LIBRARY_NAMES")
DELAY = int(os.getenv("DELAY"))
REFRESH_1970_ONLY = booler(os.getenv("REFRESH_1970_ONLY"))

if LIBRARY_NAMES:
    LIB_ARRAY = [s.strip() for s in LIBRARY_NAMES.split(",")]
else:
    LIB_ARRAY = [LIBRARY_NAME]

if LIBRARY_NAMES == 'ALL_LIBRARIES':
    LIB_ARRAY = []
    all_libs = plex.library.sections()
    for lib in all_libs:
        if lib.type in ('movie', 'show'):
            LIB_ARRAY.append(lib.title.strip())

TMDB_STR = "tmdb://"
TVDB_STR = "tvdb://"

def progress(count, total, status=""):
    """ Progress bar """
    bar_len = 40
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    p_bar = "=" * filled_len + "-" * (bar_len - filled_len)
    stat_str = textwrap.shorten(status, width=80)

    sys.stdout.write(f"[{p_bar}] {percents}% ... {stat_str.ljust(80)}\r")
    sys.stdout.flush()

for lib in LIB_ARRAY:
    print(f"getting items from [{lib}]...")
    logger(f"getting items from [{lib}]...", 'info', 'a')
    the_lib = plex.library.section(lib)
    item_total, items = get_all_from_library(the_lib)
    logger(f"looping over {item_total} items...", 'info', 'a')
    ITEM_COUNT = 1

    plex_links = []
    external_links = []

    with alive_bar(item_total, dual_line=True, title=f"Refresh Metadata: {the_lib.title}") as bar:
        for item in items:
            tmpDict = {}
            ITEM_COUNT = ITEM_COUNT + 1
            ATTEMPTS = 0

            PROGRESS_STR = f"{item.title}"

            progress(ITEM_COUNT, item_total, PROGRESS_STR)

            while ATTEMPTS < 5:
                try:

                    PROGRESS_STR = f"{item.title} - attempt {ATTEMPTS + 1}"
                    logger(PROGRESS_STR, 'info', 'a')

                    item.refresh()

                    time.sleep(DELAY)
                    PROGRESS_STR = f"{item.title} - DONE"
                    progress(ITEM_COUNT, item_total, PROGRESS_STR)

                    ATTEMPTS = 6
                except urllib3.exceptions.ReadTimeoutError:
                    progress(ITEM_COUNT, item_total, "ReadTimeoutError: " + item.title)
                except urllib3.exceptions.HTTPError:
                    progress(ITEM_COUNT, item_total, "HTTPError: " + item.title)
                except ReadTimeout:
                    progress(ITEM_COUNT, item_total, "ReadTimeout: " + item.title)
                except Exception as ex: # pylint: disable=broad-exception-caught
                    progress(ITEM_COUNT, item_total, "EX: " + item.title)
                    logging.error(ex)

                ATTEMPTS += 1

    print(os.linesep)
