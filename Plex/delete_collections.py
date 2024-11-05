""" Delete collections from a Plex library """
#!/usr/bin/env python
import os
import sys
import time
from pathlib import Path
from datetime import datetime
from helpers import get_plex, load_and_upgrade_env
from alive_progress import alive_bar

from logs import setup_logger, plogger


SCRIPT_NAME = Path(__file__).stem

VERSION = "0.1.0"

# current dateTime
now = datetime.now()

# convert to string
RUNTIME_STR = now.strftime("%Y-%m-%d %H:%M:%S")

env_file_path = Path(".env")

ACTIVITY_LOG = f"{SCRIPT_NAME}.log"

setup_logger('activity_log', ACTIVITY_LOG)

plogger(f"Starting {SCRIPT_NAME} {VERSION} at {RUNTIME_STR}", 'info', 'a')

if load_and_upgrade_env(env_file_path) < 0:
    sys.exit()

LIBRARY_NAME = os.getenv("LIBRARY_NAME")
LIBRARY_NAMES = os.getenv("LIBRARY_NAMES")
DELAY = int(os.getenv("DELAY"))
KEEP_COLLECTIONS = os.getenv("KEEP_COLLECTIONS")

if not DELAY:
    DELAY = 0

if LIBRARY_NAMES:
    LIB_ARRAY = LIBRARY_NAMES.split(",")
else:
    LIB_ARRAY = [LIBRARY_NAME]

plogger(f"Acting on libraries: {LIB_ARRAY}", 'info', 'a')

if KEEP_COLLECTIONS:
    keeper_array = KEEP_COLLECTIONS.split(",")
else:
    keeper_array = [KEEP_COLLECTIONS]

plex = get_plex()

if LIBRARY_NAMES == 'ALL_LIBRARIES':
    LIB_ARRAY = []
    all_libs = plex.library.sections()
    for lib in all_libs:
        if lib.type in ('movie', 'show'):
            LIB_ARRAY.append(lib.title.strip())

coll_obj = {}
coll_obj["collections"] = {}


def get_sort_text(argument):
    """ Get the sort text """
    switcher = {0: "release", 1: "alpha", 2: "custom"}
    return switcher.get(argument, "invalid-sort")

for lib in LIB_ARRAY:
    the_lib = plex.library.section(lib)
    items = the_lib.collections()
    item_total = len(items)
    print(f"{item_total} collection(s) retrieved...")
    with alive_bar(item_total, dual_line=True, title="Collection delete - Plex") as bar:
        for item in items:
            title = item.title

            if title in keeper_array:
                bar.text = f"-> keeping: {title}"
            else:
                bar.text = f"-> deleting: {title}"
                item.delete()

            bar() # pylint: disable=not-callable

            # Wait between items in case hammering the Plex server turns out badly.
            time.sleep(DELAY)
