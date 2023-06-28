from alive_progress import alive_bar
from plexapi.server import PlexServer
from plexapi.utils import download
from ruamel import yaml
import os
from pathlib import Path, PurePath
from dotenv import load_dotenv
import time
from tabulate import tabulate

load_dotenv()

PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')
PLEX_TIMEOUT = os.getenv('PLEX_TIMEOUT')
DELAY = int(os.getenv('DELAY'))

if not DELAY:
    DELAY = 0

if not PLEX_TIMEOUT:
    PLEX_TIMEOUT = 120

os.environ["PLEXAPI_PLEXAPI_TIMEOUT"] = str(PLEX_TIMEOUT)

plex = PlexServer(PLEX_URL, PLEX_TOKEN)

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

