#!/usr/bin/env python
import time
from datetime import datetime
from pathlib import Path

from alive_progress import alive_bar
from config import Config
from helpers import get_plex, get_redaction_list, get_target_libraries
from logs import plogger, setup_logger

SCRIPT_NAME = Path(__file__).stem

VERSION = "0.2.0"

# current dateTime
now = datetime.now()

# convert to string
RUNTIME_STR = now.strftime("%Y-%m-%d %H:%M:%S")

ACTIVITY_LOG = f"{SCRIPT_NAME}.log"

setup_logger("activity_log", ACTIVITY_LOG)

plogger(f"Starting {SCRIPT_NAME} {VERSION} at {RUNTIME_STR}", "info", "a")

config = Config('../config.yaml')

DELAY = config.get_int('general.delay')
KEEP_COLLECTIONS = config.get('delete_collection.keep_collections')

if not DELAY:
    DELAY = 0


if KEEP_COLLECTIONS:
    keeper_array = KEEP_COLLECTIONS.split(",")
else:
    keeper_array = [KEEP_COLLECTIONS]

plex = get_plex()

LIB_ARRAY = get_target_libraries(plex)

plogger(f"Acting on libraries: {LIB_ARRAY}", "info", "a")

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
