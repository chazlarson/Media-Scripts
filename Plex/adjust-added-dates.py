#!/usr/bin/env python
import json
import os
import pickle
import platform
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from multiprocessing import cpu_count
from multiprocessing.pool import ThreadPool
from pathlib import Path
from tmdbapis import TMDbAPIs
from logs import setup_logger, plogger, blogger, logger

import filetype
import piexif
import piexif.helper
import plexapi
import requests
from alive_progress import alive_bar, alive_it
from dotenv import load_dotenv
from helpers import (booler, get_all_from_library, get_ids, get_letter_dir, get_plex,
                     get_size, redact, validate_filename, load_and_upgrade_env)
from pathvalidate import ValidationError, validate_filename
from plexapi import utils
from plexapi.exceptions import Unauthorized
from plexapi.server import PlexServer
from plexapi.utils import download
from plexapi.video import Episode

SCRIPT_NAME = Path(__file__).stem

env_file_path = Path(".env")

#      0.1.1 Log config details

VERSION = "0.1.1"

# current dateTime
now = datetime.now()

# convert to string
RUNTIME_STR = now.strftime("%Y-%m-%d %H:%M:%S")

ACTIVITY_LOG = f"{SCRIPT_NAME}.log"

setup_logger('activity_log', ACTIVITY_LOG)

plogger(f"Starting {SCRIPT_NAME} {VERSION} at {RUNTIME_STR}", 'info', 'a')

if load_and_upgrade_env(env_file_path) < 0:
    exit()

plex = get_plex()

logger("connection success", 'info', 'a')

ADJUST_DATE_FUTURES_ONLY = booler(os.getenv("ADJUST_DATE_FUTURES_ONLY"))
plogger(f"ADJUST_DATE_FUTURES_ONLY: {ADJUST_DATE_FUTURES_ONLY}", 'info', 'a')

ADJUST_DATE_EPOCH_ONLY = booler(os.getenv("ADJUST_DATE_EPOCH_ONLY"))
plogger(f"ADJUST_DATE_EPOCH_ONLY: {ADJUST_DATE_EPOCH_ONLY}", 'info', 'a')

EPOCH_DATE=datetime(1970,1,1,0,0,0)

TMDB_KEY = os.getenv("TMDB_KEY")

tmdb = TMDbAPIs(TMDB_KEY, language="en")

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
        if lib.type == 'movie' or lib.type == 'show':
            LIB_ARRAY.append(lib.title.strip())

plogger(f"Acting on libraries: {LIB_ARRAY}", 'info', 'a')

def is_epoch(the_date):
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
            items = get_all_from_library(plex, the_lib, None, {"addedAt>>": TODAY_STR})
        else:
            items = get_all_from_library(plex, the_lib)

        item_total = len(items)
        if item_total > 0:
            logger(f"looping over {item_total} items...", 'info', 'a')
            item_count = 0

            plex_links = []
            external_links = []

            with alive_bar(item_total, dual_line=True, title=f"Adjust added dates {the_lib.title}") as bar:
                for item in items:
                    if item.title == "McCloud":
                        print(f"{item.title}")

                        try:
                            item_count += 1
                            added_too_far_apart = False
                            orig_too_far_apart = False
                            sub_items = [item]

                            if is_show:
                                episodes = item.episodes()
                                sub_items = sub_items + episodes

                            for sub_item in sub_items:
                                try:
                                    imdbid, tmid, tvid = get_ids(sub_item.guids, None)
                                
                                    if is_movie:
                                        tmdb_item = tmdb.movie(tmid)
                                        release_date = tmdb_item.release_date
                                    else:
                                        if sub_item.type == 'show':
                                            tmdb_item = tmdb.tv_show(tmid)
                                            release_date = tmdb_item.first_air_date
                                        else:
                                            parent_show = sub_item.show()
                                            imdbid, tmid, tvid = get_ids(parent_show.guids, None)
                                            season_num = sub_item.seasonNumber
                                            episode_num = sub_item.episodeNumber
                                
                                            tmdb_item = tmdb.tv_episode(tmid, season_num, episode_num)
                                            release_date = tmdb_item.air_date

                                    added_date = item.addedAt
                                    orig_date = item.originallyAvailableAt
                                    
                                    if not ADJUST_DATE_EPOCH_ONLY or (ADJUST_DATE_EPOCH_ONLY and is_epoch(orig_date)):
                                        try:
                                            delta = added_date - release_date
                                            added_too_far_apart = abs(delta.days) > 1
                                        except:
                                            added_too_far_apart = added_date is None and release_date is not None

                                        try:
                                            delta = orig_date - release_date
                                            orig_too_far_apart = abs(delta.days) > 1
                                        except:
                                            orig_too_far_apart = orig_date is None and release_date is not None
                                        
                                        if added_too_far_apart:
                                            try:
                                                item.addedAt = release_date
                                                blogger(f"Set {sub_item.title} added at to {release_date}", 'info', 'a', bar)
                                            except Exception as ex:
                                                plogger(f"Problem processing {item.title}; {ex}", 'info', 'a')
                
                                        if orig_too_far_apart:
                                            try:
                                                item.originallyAvailableAt = release_date
                                                blogger(f"Set {sub_item.title} originally available at to {release_date}", 'info', 'a', bar)
                                            except Exception as ex:
                                                plogger(f"Problem processing {item.title}; {ex}", 'info', 'a')
        
                                    else:
                                        blogger(f"skipping {item.title}: EPOCH_ONLY {ADJUST_DATE_EPOCH_ONLY}, originally available date {orig_date}", 'info', 'a', bar)

                                except Exception as ex:
                                    plogger(f"Problem processing sub_item {item.title}; {ex}", 'info', 'a')

                        except Exception as ex:
                            plogger(f"Problem processing {item.title}; {ex}", 'info', 'a')

                    bar()
                    
            plogger(f"Processed {item_count} of {item_total}", 'info', 'a')

        progress_str = "COMPLETE"
        logger(progress_str, 'info', 'a')

    except Exception as ex:
        progress_str = f"Problem processing {lib}; {ex}"
        plogger(progress_str, 'info', 'a')