from alive_progress import alive_bar
from plexapi.server import PlexServer
from plexapi.utils import download
from ruamel import yaml
import os
from pathlib import Path, PurePath
from dotenv import load_dotenv
import time
from helpers import get_plex, load_and_upgrade_env

from datetime import datetime, timedelta
# current dateTime
now = datetime.now()

# convert to string
RUNTIME_STR = now.strftime("%Y-%m-%d %H:%M:%S")

env_file_path = Path(".env")

status = load_and_upgrade_env(env_file_path)

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
    item_count = 1
    with alive_bar(item_total, dual_line=True, title='Collection list - Plex') as bar:
        for item in items:
            title = item.title
            print(f"{title}")

            bar()

            # Wait between items in case hammering the Plex server turns out badly.
            time.sleep(DELAY)

