""" List all collections in a Plex library """
#!/usr/bin/env python
import logging
import os
import sys
from pathlib import Path
import time
from datetime import datetime
from helpers import get_plex, load_and_upgrade_env
from alive_progress import alive_bar

SCRIPT_NAME = Path(__file__).stem

VERSION = "0.1.0"

# current dateTime
now = datetime.now()

# convert to string
RUNTIME_STR = now.strftime("%Y-%m-%d %H:%M:%S")

env_file_path = Path(".env")

logging.basicConfig(
    filename=f"{SCRIPT_NAME}.log",
    filemode="w",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

START_STR = f"Starting {SCRIPT_NAME} {VERSION} at {RUNTIME_STR}"
logging.info(START_STR)
print(START_STR)

if load_and_upgrade_env(env_file_path) < 0:
    sys.exit()

LIBRARY_NAME = os.getenv('LIBRARY_NAME')
LIBRARY_NAMES = os.getenv('LIBRARY_NAMES')
DELAY = int(os.getenv('DELAY'))

if not DELAY:
    DELAY = 0

if LIBRARY_NAMES:
    lib_array = LIBRARY_NAMES.split(",")
else:
    lib_array = [LIBRARY_NAME]

plex = get_plex()

coll_obj = {}
coll_obj['collections'] = {}

def get_sort_text(argument):
    """ Function to return the sort text for the given sort value """
    switcher = {
        0: "release",
        1: "alpha",
        2: "custom"
    }
    return switcher.get(argument, "invalid-sort")

for lib in lib_array:
    print(f"{lib} collection(s):")
    movies = plex.library.section(lib)
    items = movies.collections()
    item_total = len(items)
    print(f"{item_total} collection(s) retrieved...")

    with alive_bar(item_total, dual_line=True, title='Collection list - Plex') as bar:
        for item in items:
            title = item.title
            print(f"{title}")

            bar() # pylint: disable=not-callable

            # Wait between items in case hammering the Plex server turns out badly.
            time.sleep(DELAY)
