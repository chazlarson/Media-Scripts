#!/usr/bin/env python
import logging
import time
from datetime import datetime
from pathlib import Path

from alive_progress import alive_bar
from config import Config
from helpers import get_plex, get_redaction_list, get_target_libraries

SCRIPT_NAME = Path(__file__).stem

VERSION = "0.1.0"

# current dateTime
now = datetime.now()

# convert to string
RUNTIME_STR = now.strftime("%Y-%m-%d %H:%M:%S")

logging.basicConfig(
    filename=f"{SCRIPT_NAME}.log",
    filemode="w",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logging.info(f"Starting {SCRIPT_NAME} {VERSION} at {RUNTIME_STR}")
print(f"Starting {SCRIPT_NAME} {VERSION} at {RUNTIME_STR}")

config = Config('../config.yaml')

DELAY = config.get_int("settings.delay", 0)

plex = get_plex()

LIB_ARRAY = get_target_libraries(plex)

coll_obj = {}
coll_obj["collections"] = {}


def get_sort_text(argument):
    switcher = {0: "release", 1: "alpha", 2: "custom"}
    return switcher.get(argument, "invalid-sort")


for lib in LIB_ARRAY:
    print(f"{lib} collection(s):")
    movies = plex.library.section(lib)
    items = movies.collections()
    item_total = len(items)
    print(f"{item_total} collection(s) retrieved...")
    item_count = 1
    with alive_bar(item_total, dual_line=True, title="Collection list - Plex") as bar:
        for item in items:
            title = item.title
            print(f"{title}")

            bar()

            # Wait between items in case hammering the Plex server turns out badly.
            time.sleep(DELAY)
