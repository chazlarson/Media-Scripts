#!/usr/bin/env python
import time
from datetime import datetime
from pathlib import Path

from alive_progress import alive_bar
from config import Config
from helpers import get_plex, get_target_libraries
from logs import plogger, setup_logger

SCRIPT_NAME = Path(__file__).stem

VERSION = "0.2.1"

# 0.2.0 config class
# 0.2.1 delete collections whose titles contain a substring

# current dateTime
now = datetime.now()

# convert to string
RUNTIME_STR = now.strftime("%Y-%m-%d %H:%M:%S")

ACTIVITY_LOG = f"{SCRIPT_NAME}.log"

def get_sort_text(argument):
    switcher = {0: "release", 1: "alpha", 2: "custom"}
    return switcher.get(argument, "invalid-sort")


def collection_should_delete(title, keeper_array, containing):
    """Keep listed titles. Otherwise delete all, or only titles containing a substring."""
    if title in keeper_array:
        return False
    if containing:
        return title.find(containing) > -1
    return True


def main():
    setup_logger("activity_log", ACTIVITY_LOG)
    plogger(f"Starting {SCRIPT_NAME} {VERSION} at {RUNTIME_STR}", "info", "a")

    config = Config('../config.yaml')

    delay = config.get_int('general.delay')
    keep_collections = config.get('delete_collection.keep_collections')
    delete_collections_containing = config.get(
        'delete_collection.delete_collections_containing'
    )

    if not delay:
        delay = 0

    if keep_collections:
        keeper_array = keep_collections.split(",")
    else:
        keeper_array = [keep_collections]

    plex = get_plex()
    lib_array = get_target_libraries(plex)

    plogger(f"Acting on libraries: {lib_array}", "info", "a")

    for lib in lib_array:
        the_lib = plex.library.section(lib)
        items = the_lib.collections()
        item_total = len(items)
        print(f"{item_total} collection(s) retrieved...")
        with alive_bar(item_total, dual_line=True, title="Collection delete - Plex") as bar:
            for item in items:
                title = item.title

                if title in keeper_array:
                    bar.text = f"-> keeping: {title}"
                elif collection_should_delete(
                    title, keeper_array, delete_collections_containing
                ):
                    bar.text = f"-> deleting: {title}"
                    item.delete()

                bar()

                # Wait between items in case hammering the Plex server turns out badly.
                time.sleep(delay)


if __name__ == "__main__":
    main()
