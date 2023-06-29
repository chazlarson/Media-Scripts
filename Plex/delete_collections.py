from alive_progress import alive_bar
from plexapi.server import PlexServer
import os
from dotenv import load_dotenv
import time
from helpers import get_plex, load_and_upgrade_env

import logging
from pathlib import Path
from datetime import datetime
# current dateTime
now = datetime.now()

# convert to string
RUNTIME_STR = now.strftime("%Y-%m-%d %H:%M:%S")

SCRIPT_NAME = Path(__file__).stem

env_file_path = Path(".env")

logging.basicConfig(
    filename=f"{SCRIPT_NAME}.log",
    filemode="w",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logging.info(f"Starting {SCRIPT_NAME}")
print(f"Starting {SCRIPT_NAME}")

status = load_and_upgrade_env(env_file_path)

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

if KEEP_COLLECTIONS:
    keeper_array = KEEP_COLLECTIONS.split(",")
else:
    keeper_array = [KEEP_COLLECTIONS]

plex = get_plex()

if LIBRARY_NAMES == 'ALL_LIBRARIES':
    LIB_ARRAY = []
    all_libs = plex.library.sections()
    for lib in all_libs:
        if lib.type == 'movie' or lib.type == 'show':
            LIB_ARRAY.append(lib.title.strip())

coll_obj = {}
coll_obj["collections"] = {}


def get_sort_text(argument):
    switcher = {0: "release", 1: "alpha", 2: "custom"}
    return switcher.get(argument, "invalid-sort")

for lib in LIB_ARRAY:
    the_lib = plex.library.section(lib)
    items = the_lib.collections()
    item_total = len(items)
    print(f"{item_total} collection(s) retrieved...")
    item_count = 1
    with alive_bar(item_total, dual_line=True, title="Collection delete - Plex") as bar:
        for item in items:
            title = item.title

            if title in keeper_array:
                bar.text = f"-> keeping: {title}"
            else:
                bar.text = f"-> deleting: {title}"
                item.delete()

            bar()

            # Wait between items in case hammering the Plex server turns out badly.
            time.sleep(DELAY)
