#!/usr/bin/env python
import os
import platform
from datetime import datetime
from pathlib import Path

from alive_progress import alive_bar
from config import Config
from helpers import (get_all_from_library, get_ids, get_plex,
                     get_target_libraries)
from logs import logger, plogger, setup_logger

SCRIPT_NAME = Path(__file__).stem

VERSION = "0.1.0"

# current dateTime
now = datetime.now()

IS_WINDOWS = platform.system() == "Windows"

# convert to string
RUNTIME_STR = now.strftime("%Y-%m-%d %H:%M:%S")

ACTIVITY_LOG = f"{SCRIPT_NAME}.log"
DOWNLOAD_LOG = f"{SCRIPT_NAME}-dl.log"
SUPERCHAT = False


def superchat(msg, level, logfile):
    if SUPERCHAT:
        logger(msg, level, logfile)


setup_logger("activity_log", ACTIVITY_LOG)
setup_logger("download_log", DOWNLOAD_LOG)

plogger(f"Starting {SCRIPT_NAME} {VERSION} at {RUNTIME_STR}", "info", "a")

config = Config('../config.yaml')

ID_FILES = True

URL_ARRAY = []
# no one using this yet
# QUEUED_DOWNLOADS = {}

POSTER_DIR = config.get("image_download.where_to_put_it.poster_dir", "extracted_posters")


SUPERCHAT = config.get("general.superchat", False)

INCLUDE_COLLECTION_MEMBERS = config.get_bool("list_item_ids.include_collection_members", False)
ONLY_COLLECTION_MEMBERS = config.get_bool("list_item_ids.only_collection_members", False)
DELAY = config.get_int("general.delay", 0)

ONLY_THESE_COLLECTIONS = config.get("list_item_ids.only_these_collections", "").strip()

if ONLY_THESE_COLLECTIONS:
    COLLECTION_ARRAY = [s.strip() for s in ONLY_THESE_COLLECTIONS.split("|")]
else:
    COLLECTION_ARRAY = []

redaction_list = get_redaction_list()
plex = get_plex()

LIB_ARRAY = get_target_libraries(plex)


def lib_type_supported(lib):
    return lib.type == "movie" or lib.type == "show"


for lib in LIB_ARRAY:
    try:
        highwater = 0

        plogger(f"Loading {lib} ...", "info", "a")
        the_lib = plex.library.section(lib)
        if lib_type_supported(the_lib):
            the_uuid = the_lib.uuid
            superchat(f"{the_lib} uuid {the_uuid}", "info", "a")
            ID_ARRAY = []
            the_title = the_lib.title
            superchat(f"This library is called {the_title}", "info", "a")

            if INCLUDE_COLLECTION_MEMBERS:
                plogger(f"getting collections from [{lib}]...", "info", "a")

                items = the_lib.collections()
                item_total = len(items)
                plogger(f"{item_total} collection(s) retrieved...", "info", "a")

                tgt_ext = ".dat"

                if item_total > 0:
                    with alive_bar(
                        item_total, dual_line=True, title="Grab Collection details"
                    ) as bar:
                        for item in items:
                            plogger(
                                f"This collection is called {item.title}", "info", "a"
                            )

                            collection_items = item.items()
                            coll_item_total = len(collection_items)
                            coll_idx = 1
                            for collection_item in collection_items:
                                imdbid, tmid, tvid = get_ids(collection_item.guids)
                                if the_lib.TYPE == "movie":
                                    plogger(
                                        f"Collection: {item.title} item {coll_idx: >5}/{coll_item_total: >5} | TMDb ID: {tmid: >7}    | IMDb ID: {imdbid: >10}  | {collection_item.title}",
                                        "info",
                                        "a",
                                    )
                                else:
                                    plogger(
                                        f"Collection: {item.title} item {coll_idx: >5}/{coll_item_total: >5} | TVDb ID: {tvid: >6}    | IMDb ID: {imdbid: >10}  | {collection_item.title}",
                                        "info",
                                        "a",
                                    )
                                coll_idx += 1
                            bar()

            else:
                plogger("Skipping collection members ...", "info", "a")

            if not ONLY_COLLECTION_MEMBERS:
                if len(COLLECTION_ARRAY) == 0:
                    COLLECTION_ARRAY = ["placeholder_collection_name"]

                for coll in COLLECTION_ARRAY:
                    lib_key = f"{the_uuid}-{coll}"

                    items = []

                    if coll == "placeholder_collection_name":
                        plogger(f"Loading {the_lib.TYPE}s  ...", "info", "a")
                        item_total, items = get_all_from_library(the_lib, None, None)
                        plogger(
                            f"Completed loading {len(items)} of {the_lib.totalViewSize()} {the_lib.TYPE}(s) from {the_lib.title}",
                            "info",
                            "a",
                        )

                    else:
                        plogger(
                            f"Loading everything in collection {coll} ...", "info", "a"
                        )
                        item_total, items = get_all_from_library(
                            the_lib, None, {"collection": coll}
                        )
                        plogger(
                            f"Completed loading {len(items)} from collection {coll}",
                            "info",
                            "a",
                        )

                    if item_total > 0:
                        logger(f"looping over {item_total} items...", "info", "a")
                        item_count = 0

                        plex_links = []
                        external_links = []

                        with alive_bar(
                            item_total,
                            dual_line=True,
                            title=f"Grab all posters {the_lib.title}",
                        ) as bar:
                            for item in items:
                                try:
                                    imdbid, tmid, tvid = get_ids(item.guids)
                                    imdbid_format = (
                                        f"{imdbid: >10}" if imdbid else "       N/A"
                                    )
                                    tmid_format = f"{tmid: >7}" if tmid else "    N/A"
                                    tvid_format = f"{tvid: >6}" if imdbid else "   N/A"

                                    if the_lib.TYPE == "movie":
                                        plogger(
                                            f"item {item_count: >5}/{item_total: >5} | TMDb ID: {tmid_format}    | IMDb ID: {imdbid_format}  | {item.title}",
                                            "info",
                                            "a",
                                        )
                                    else:
                                        plogger(
                                            f"item {item_count: >5}/{item_total: >5} | TVDb ID: {tvid_format}    | IMDb ID: {imdbid_format}  | {item.title}",
                                            "info",
                                            "a",
                                        )

                                    item_count += 1
                                except Exception as ex:
                                    plogger(
                                        f"Problem processing {item.title}; {ex}",
                                        "info",
                                        "a",
                                    )

                                bar()

                        plogger(f"Processed {item_count} of {item_total}", "info", "a")

            progress_str = "COMPLETE"
            logger(progress_str, "info", "a")
        else:
            logger(f"Library type '{the_lib.type}' not supported", "info", "a")

    except Exception as ex:
        progress_str = f"Problem processing {lib}; {ex}"
        plogger(progress_str, "info", "a")

plogger("Complete!", "info", "a")
