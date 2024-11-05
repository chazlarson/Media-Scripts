""" module to adjust added dates to match release dates """
#!/usr/bin/env python
import os
import sys
from datetime import datetime
from pathlib import Path
from tmdbapis import TMDbAPIs
from alive_progress import alive_bar
from logs import setup_logger, plogger, blogger, logger

from helpers import (booler, get_all_from_library, get_ids_local, get_plex,
                    load_and_upgrade_env)

SCRIPT_NAME = Path(__file__).stem

env_file_path = Path(".env")

#      0.1.1 Log config details
#      0.1.2 incorporate helper changes, remove testing code

VERSION = "0.1.2"

# current dateTime
now = datetime.now()

# convert to string
RUNTIME_STR = now.strftime("%Y-%m-%d %H:%M:%S")

ACTIVITY_LOG = f"{SCRIPT_NAME}.log"

setup_logger('activity_log', ACTIVITY_LOG)

plogger(f"Starting {SCRIPT_NAME} {VERSION} at {RUNTIME_STR}", 'info', 'a')

if load_and_upgrade_env(env_file_path) < 0:
    sys.exit()

plex = get_plex()

logger("connection success", 'info', 'a')

ADJUST_DATE_FUTURES_ONLY = booler(os.getenv("ADJUST_DATE_FUTURES_ONLY"))
plogger(f"ADJUST_DATE_FUTURES_ONLY: {ADJUST_DATE_FUTURES_ONLY}", 'info', 'a')

ADJUST_DATE_EPOCH_ONLY = booler(os.getenv("ADJUST_DATE_EPOCH_ONLY"))
plogger(f"ADJUST_DATE_EPOCH_ONLY: {ADJUST_DATE_EPOCH_ONLY}", 'info', 'a')

EPOCH_DATE=datetime(1970,1,1,0,0,0)

tmdb_key = os.getenv("TMDB_KEY")

tmdb = TMDbAPIs(tmdb_key, language="en")

LIBRARY_NAME = os.getenv("LIBRARY_NAME")
LIBRARY_NAMES = os.getenv("LIBRARY_NAMES")

if LIBRARY_NAMES:
    LIB_ARRAY = [s.strip() for s in LIBRARY_NAMES.split(",")]
else:
    LIB_ARRAY = [LIBRARY_NAME]

if LIBRARY_NAMES == 'ALL_LIBRARIES':
    LIB_ARRAY = []
    all_libs = plex.library.sections()
    for lib in all_libs:
        if lib.type in ('movie', 'show'):
            LIB_ARRAY.append(lib.title.strip())

plogger(f"Acting on libraries: {LIB_ARRAY}", 'info', 'a')

def is_epoch(the_date):
    """docstring placeholder"""
    ret_val = False

    if the_date is not None:
        ret_val = the_date.year == 1970 and the_date.month == 1 and the_date.day == 1

    return ret_val

for lib in LIB_ARRAY:
    try:
        plogger(f"Loading {lib} ...", 'info', 'a')
        the_lib = plex.library.section(lib)
        is_movie = the_lib.type == 'movie'
        is_show = the_lib.type == 'show'

        if not is_movie:
            print("the script hasn't been tested with non-movie libraries, skipping.")
            # continue

        lib_size = the_lib.totalViewSize()

        if ADJUST_DATE_FUTURES_ONLY:
            TODAY_STR = now.strftime("%Y-%m-%d")
            item_count, items = get_all_from_library(the_lib, None, {"addedAt>>": TODAY_STR})
        else:
            item_count, items = get_all_from_library(the_lib)

        if item_count > 0:
            logger(f"looping over {item_count} items...", 'info', 'a')
            ITEMS_PROCESSED = 0

            plex_links = []
            external_links = []

            with alive_bar(item_count, dual_line=True, title=f"Adjust added dates {the_lib.title}") as bar:
                for item in items:
                    try:
                        ITEMS_PROCESSED += 1
                        ADDED_TOO_FAR_APART = False
                        ORIG_TOO_FAR_APART = False
                        sub_items = [item]

                        if is_show:
                            episodes = item.episodes()
                            sub_items = sub_items + episodes

                        for sub_item in sub_items:
                            try:
                                imdbid, tmid, tvid = get_ids_local(sub_item.guids)

                                if is_movie:
                                    tmdb_item = tmdb.movie(tmid)
                                    release_date = tmdb_item.release_date
                                else:
                                    if sub_item.type == 'show':
                                        tmdb_item = tmdb.tv_show(tmid)
                                        release_date = tmdb_item.first_air_date
                                    else:
                                        parent_show = sub_item.show()
                                        imdbid, tmid, tvid = get_ids_local(parent_show.guids)
                                        season_num = sub_item.seasonNumber
                                        episode_num = sub_item.episodeNumber

                                        tmdb_item = tmdb.tv_episode(tmid, season_num, episode_num)
                                        release_date = tmdb_item.air_date

                                added_date = item.addedAt
                                orig_date = item.originallyAvailableAt

                                if not ADJUST_DATE_EPOCH_ONLY or (ADJUST_DATE_EPOCH_ONLY and is_epoch(orig_date)):
                                    try:
                                        delta = added_date - release_date
                                        ADDED_TOO_FAR_APART = abs(delta.days) > 1
                                    except: # pylint: disable=bare-except
                                        ADDED_TOO_FAR_APART = added_date is None and release_date is not None

                                    try:
                                        delta = orig_date - release_date
                                        ORIG_TOO_FAR_APART = abs(delta.days) > 1
                                    except: # pylint: disable=bare-except
                                        ORIG_TOO_FAR_APART = orig_date is None and release_date is not None

                                    if ADDED_TOO_FAR_APART:
                                        try:
                                            item.addedAt = release_date
                                            blogger(f"Set {sub_item.title} added at to {release_date}", 'info', 'a', bar)
                                        except Exception as ex: # pylint: disable=broad-exception-caught
                                            plogger(f"Problem processing {item.title}; {ex}", 'info', 'a')

                                    if ORIG_TOO_FAR_APART:
                                        try:
                                            item.originallyAvailableAt = release_date
                                            blogger(f"Set {sub_item.title} originally available at to {release_date}", 'info', 'a', bar)
                                        except Exception as ex: # pylint: disable=broad-exception-caught
                                            plogger(f"Problem processing {item.title}; {ex}", 'info', 'a')

                                else:
                                    blogger(f"skipping {item.title}: EPOCH_ONLY {ADJUST_DATE_EPOCH_ONLY}, originally available date {orig_date}", 'info', 'a', bar)

                            except Exception as ex: # pylint: disable=broad-exception-caught
                                plogger(f"Problem processing sub_item {item.title}; {ex}", 'info', 'a')

                    except Exception as ex: # pylint: disable=broad-exception-caught
                        plogger(f"Problem processing {item.title}; {ex}", 'info', 'a')

                    bar() # pylint: disable=not-callable

            plogger(f"Processed {ITEMS_PROCESSED} of {item_count}", 'info', 'a')

        logger("COMPLETE", 'info', 'a')

    except Exception as ex: # pylint: disable=broad-exception-caught
        plogger(f"Problem processing {lib}; {ex}", 'info', 'a')
