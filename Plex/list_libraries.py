from alive_progress import alive_bar
from plexapi.server import PlexServer
from plexapi.utils import download
from ruamel import yaml
import os
from pathlib import Path, PurePath
from dotenv import load_dotenv
import time
from tabulate import tabulate
from helpers import get_plex, load_and_upgrade_env

from datetime import datetime, timedelta
# current dateTime
now = datetime.now()

# convert to string
RUNTIME_STR = now.strftime("%Y-%m-%d %H:%M:%S")

env_file_path = Path(".env")

if load_and_upgrade_env(env_file_path) < 0:
    exit()

DELAY = int(os.getenv('DELAY'))

if not DELAY:
    DELAY = 0

plex = get_plex()

coll_obj = {}
coll_obj['libraries'] = {}

def get_sort_text(argument):
    switcher = {
        0: "release",
        1: "alpha",
        2: "custom"
    }
    return switcher.get(argument, "invalid-sort")

sections = plex.library.sections()
item_total = len(sections)
table = [['Name', 'Type', 'Size']]

with alive_bar(item_total, dual_line=True, title='Library list - Plex') as bar:
    for section in sections:
        info = []
        info.append(section.title)
        info.append(section.type)
        info.append(section.totalSize)

        table.append(info)

        bar()

        # Wait between items in case hammering the Plex server turns out badly.
        time.sleep(DELAY)
    
print(tabulate(table, headers='firstrow', tablefmt='fancy_grid'))

