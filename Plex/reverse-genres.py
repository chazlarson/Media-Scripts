#!/usr/bin/env python
import os
from datetime import datetime
from pathlib import Path

from alive_progress import alive_bar
from logs import logger, plogger, setup_logger

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mediascripts.config import Config  # noqa: E402
from mediascripts.helpers import (get_all_from_library, get_plex, get_target_libraries)  # noqa: E402

def reverse_genres(item):
    reversed_list = []

    item.reload()
    genres = item.genres

    print(f"{item.title} before: {genres}")

    item.removeGenre(genres)

    for genre in genres:
        reversed_list.insert(0, genre)

    print(f"{item.title} reversed: {reversed_list}")

    for genre in reversed_list:
        print(f"{item.title} adding: {genre}")
        item.addGenre(genre)
        item.reload()

    item.reload()
    new_genres = item.genres

    print(f"{item.title} after: {new_genres}")

def main():
    global now, RUNTIME_STR, SCRIPT_NAME, VERSION, ACTIVITY_LOG, config, NEW, UPDATED
    global plex, LIB_ARRAY, lib, the_lib, count, item_total, items, item_count
    global plex_links, external_links, bar, item, progress_str

    # current dateTime
    now = datetime.now()

    # convert to string
    RUNTIME_STR = now.strftime("%Y-%m-%d %H:%M:%S")

    SCRIPT_NAME = Path(__file__).stem

    VERSION = "0.1.0"

    ACTIVITY_LOG = f"{SCRIPT_NAME}.log"
    setup_logger("activity_log", ACTIVITY_LOG)

    plogger(f"Starting {SCRIPT_NAME} {VERSION} at {RUNTIME_STR}", "info", "a")

    config = Config('../config.yaml')

    NEW = []
    UPDATED = []

    plex = get_plex()

    LIB_ARRAY = get_target_libraries(plex)


    for lib in LIB_ARRAY:
        try:
            the_lib = plex.library.section(lib)

            count = plex.library.section(lib).totalSize
            print(f"getting {count} {the_lib.type}s from [{lib}]...")
            logger((f"getting {count} {the_lib.type}s from [{lib}]..."), "info", "a")
            item_total, items = get_all_from_library(the_lib)
            logger((f"looping over {item_total} items..."), "info", "a")
            item_count = 1

            plex_links = []
            external_links = []

            with alive_bar(item_total, dual_line=True, title="Reverse Genres") as bar:
                for item in items:
                    logger(("================================"), "info", "a")
                    logger((f"Starting {item.title}"), "info", "a")

                    reverse_genres(item)

                    bar()

            progress_str = "COMPLETE"
            logger((progress_str), "info", "a")

            bar.text = progress_str

            print(os.linesep)

        except Exception as ex:
            progress_str = f"Problem processing {lib}; {ex}"
            logger((progress_str), "info", "a")

            print(progress_str)


if __name__ == "__main__":
    main()
