#!/usr/bin/env python
import logging
import os
from pathlib import Path

from alive_progress import alive_bar

from helpers import get_all_from_library, get_ids, get_plex, load_and_upgrade_env

import logging
from pathlib import Path
from datetime import datetime

from database import get_completed, get_count, insert_record, update_record, get_diffs

# current dateTime
now = datetime.now()

# convert to string
RUNTIME_STR = now.strftime("%Y-%m-%d %H:%M:%S")

SCRIPT_NAME = Path(__file__).stem

VERSION = "0.1.1"

# 0.1.1 refactoring changes
# 0.2.0 get rid of sqlalchemy, use the same database module as the others

env_file_path = Path(".env")

logging.basicConfig(
    filename=f"{SCRIPT_NAME}.log",
    filemode="w",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logging.info(f"Starting {SCRIPT_NAME}")
print(f"Starting {SCRIPT_NAME}")

if load_and_upgrade_env(env_file_path) < 0:
    exit()

LIBRARY_NAME = os.getenv("LIBRARY_NAME")
LIBRARY_NAMES = os.getenv("LIBRARY_NAMES")
TMDB_KEY = os.getenv("TMDB_KEY")
NEW = []
UPDATED = []

if LIBRARY_NAMES:
    LIB_ARRAY = [s.strip() for s in LIBRARY_NAMES.split(",")]
else:
    LIB_ARRAY = [LIBRARY_NAME]

CHANGE_FILE_NAME = "changes.txt"
change_file = Path(CHANGE_FILE_NAME)
# Delete any existing change file
if change_file.is_file():
    change_file.unlink()

plex = get_plex()

logging.info("connection success")


def get_IDs(type, item):
    imdbid = None
    tmid = None
    tvid = None
    raw_guid = item.guid
    bits = raw_guid.split("/")
    # plex://movie/5d776b59ad5437001f79c6f8
    # local://3961921
    if bits[0] == "plex:":
        try:
            guid = bits[3]

            if guid not in COMPLETE_ARRAY:
                try:
                    if item.type != "collection":
                        logging.info("Getting IDs")
                        imdbid, tmid, tvid = get_ids(item.guids, TMDB_KEY)
                        complete = (
                            imdbid is not None and tmid is not None and tvid is not None
                        )
                        payload = {
                            "guid": guid,
                            "imdb": imdbid,
                            "tmdb": tmid,
                            "tvdb": tvid,
                            "title": item.title,
                            "year": item.year,
                            "type": type,
                            "complete": complete,
                        }

                        diffs = get_diffs(payload)

                        if diffs["new"] or diffs["updated"]:
                            # record change
                            if diffs["new"]:
                                action = "new"
                                NEW.append(guid)
                                insert_record(payload)
                            else:
                                action = "updated"
                                UPDATED.append(guid)
                                update_record(payload)

                            with open(change_file, "a", encoding="utf-8") as cf:
                                cf.write(f"{action} - {payload} {os.linesep}")

                except Exception as ex:
                    print(f"{item.ratingKey}- {item.title} - Exception: {ex}")
                    logging.info(
                        f"EXCEPTION: {item.ratingKey}- {item.title} - Exception: {ex}"
                    )
            else:
                logging.info(f"{guid} already complete")
        except Exception:
            logging.info(f"No guid: {bits}")


COMPLETE_ARRAY = []

if LIBRARY_NAMES == "ALL_LIBRARIES":
    LIB_ARRAY = []
    all_libs = plex.library.sections()
    for lib in all_libs:
        if lib.type == "movie" or lib.type == "show":
            LIB_ARRAY.append(lib.title.strip())

with open(change_file, "a", encoding="utf-8") as cf:
    cf.write(f"start: {get_count()} records{os.linesep}")

for lib in LIB_ARRAY:
    completed_things = get_completed()

    for thing in completed_things:
        COMPLETE_ARRAY.append(thing[0])

    try:
        the_lib = plex.library.section(lib)

        count = plex.library.section(lib).totalSize
        print(f"getting {count} {the_lib.type}s from [{lib}]...")
        logging.info(f"getting {count} {the_lib.type}s from [{lib}]...")
        item_total, items = get_all_from_library(the_lib, the_lib.type)
        logging.info(f"looping over {item_total} items...")
        item_count = 1

        plex_links = []
        external_links = []

        with alive_bar(item_total, dual_line=True, title="Grab all IDs") as bar:
            for item in items:
                logging.info("================================")
                logging.info(f"Starting {item.title}")

                get_IDs(the_lib.type, item)

                bar()

        progress_str = "COMPLETE"
        logging.info(progress_str)

        bar.text = progress_str

        print(os.linesep)

    except Exception as ex:
        progress_str = f"Problem processing {lib}; {ex}"
        logging.info(progress_str)

        print(progress_str)

logging.info("================================")
logging.info(f"NEW: {len(NEW)}; UPDATED: {len(UPDATED)}")
print(f"NEW: {len(NEW)}; UPDATED: {len(UPDATED)}")

with open(change_file, "a", encoding="utf-8") as cf:
    cf.write(f"end: {get_count()} records{os.linesep}")
