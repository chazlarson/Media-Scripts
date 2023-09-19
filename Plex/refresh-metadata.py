from plexapi.server import PlexServer
import os
from dotenv import load_dotenv
import sys
import textwrap
import time
import logging
import urllib3.exceptions
from urllib3.exceptions import ReadTimeoutError
from requests import ReadTimeout
from helpers import get_plex, load_and_upgrade_env, get_all_from_library, booler
from alive_progress import alive_bar, alive_it

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
        if lib.type == 'movie' or lib.type == 'show':
            LIB_ARRAY.append(lib.title.strip())

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

for lib in LIB_ARRAY:
    print(f"getting items from [{lib}]...")
    logger(f"getting items from [{lib}]...", 'info', 'a')
    the_lib = plex.library.section(lib)
    items = get_all_from_library(plex, the_lib)
    item_total = len(items)
    logger(f"looping over {item_total} items...", 'info', 'a')
    item_count = 1

    plex_links = []
    external_links = []

    with alive_bar(item_total, dual_line=True, title=f"Adjust added dates {the_lib.title}") as bar:
        for item in items:
            tmpDict = {}
            item_count = item_count + 1
            attempts = 0

            progress_str = f"{item.title}"

            progress(item_count, item_total, progress_str)

            while attempts < 5:
                try:

                    progress_str = f"{item.title} - attempt {attempts + 1}"
                    logger(progress_str, 'info', 'a')

                    item.refresh()
                    
                    time.sleep(DELAY)
                    progress_str = f"{item.title} - DONE"
                    progress(item_count, item_total, progress_str)

                    attempts = 6
                except urllib3.exceptions.ReadTimeoutError:
                    progress(item_count, item_total, "ReadTimeoutError: " + item.title)
                except urllib3.exceptions.HTTPError:
                    progress(item_count, item_total, "HTTPError: " + item.title)
                except ReadTimeoutError:
                    progress(item_count, item_total, "ReadTimeoutError-2: " + item.title)
                except ReadTimeout:
                    progress(item_count, item_total, "ReadTimeout: " + item.title)
                except Exception as ex:
                    progress(item_count, item_total, "EX: " + item.title)
                    logging.error(ex)

                attempts += 1

    print(os.linesep)
