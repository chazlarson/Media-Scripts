""" List all libraries in Plex server """
#!/usr/bin/env python
import os
import sys
from pathlib import Path
import time
from datetime import datetime
from tabulate import tabulate
from helpers import get_plex, load_and_upgrade_env
from alive_progress import alive_bar

# current dateTime
now = datetime.now()

# convert to string
RUNTIME_STR = now.strftime("%Y-%m-%d %H:%M:%S")

env_file_path = Path(".env")

if load_and_upgrade_env(env_file_path) < 0:
    sys.exit()

DELAY = int(os.getenv('DELAY'))

if not DELAY:
    DELAY = 0

plex = get_plex()

coll_obj = {}
coll_obj['libraries'] = {}

def get_sort_text(argument):
    """ Function to return the sort text """
    switcher = {
        0: "release",
        1: "alpha",
        2: "custom"
    }
    return switcher.get(argument, "invalid-sort")

sections = plex.library.sections()
ITEM_TOTAL = len(sections)
table = [['Name', 'Type', 'Size']]

with alive_bar(ITEM_TOTAL, dual_line=True, title='Library list - Plex') as bar:
    for section in sections:
        info = []
        info.append(section.title)
        info.append(section.type)
        info.append(section.totalSize)

        table.append(info)

        bar() # pylint: disable=not-callable

        # Wait between items in case hammering the Plex server turns out badly.
        time.sleep(DELAY)

print(tabulate(table, headers='firstrow', tablefmt='fancy_grid'))
