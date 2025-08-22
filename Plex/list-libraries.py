#!/usr/bin/env python
import time
from datetime import datetime

from alive_progress import alive_bar
from config import Config
from helpers import get_plex
from tabulate import tabulate

config = Config('../config.yaml')

# current dateTime
now = datetime.now()

# convert to string
RUNTIME_STR = now.strftime("%Y-%m-%d %H:%M:%S")

DELAY = config.get_int("general.delay", 0)

plex = get_plex()

coll_obj = {}
coll_obj["libraries"] = {}


sections = plex.library.sections()
item_total = len(sections)

table = [["Key", "Name", "Type", "Agent", "Scanner", "Created At", "Updated At", "Total Size", "UUID"]]

with alive_bar(item_total, dual_line=True, title="Library list - Plex") as bar:
    for section in sections:
        info = []
        info.append(section.key)
        info.append(section.title)
        info.append(section.type)
        info.append(section.agent)
        info.append(section.scanner)
        info.append(section.createdAt.strftime("%Y-%m-%d %H:%M:%S"))
        info.append(section.updatedAt.strftime("%Y-%m-%d %H:%M:%S"))
        info.append(section.totalSize)
        info.append(section.uuid)

        table.append(info)

        bar()

        # Wait between items in case hammering the Plex server turns out badly.
        time.sleep(DELAY)

print(tabulate(table, headers="firstrow", tablefmt="fancy_grid"))
