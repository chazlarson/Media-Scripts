import json
import os
import pickle
import platform
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from multiprocessing import cpu_count
from multiprocessing.pool import ThreadPool
from pathlib import Path
from logs import setup_logger, plogger, blogger, logger

import filetype
import piexif
import piexif.helper
import plexapi
import requests
from alive_progress import alive_bar, alive_it
from dotenv import load_dotenv
from helpers import (booler, get_all_from_library, get_ids, get_letter_dir, get_plex, has_overlay, get_size, redact, validate_filename, load_and_upgrade_env)
from pathvalidate import ValidationError, is_valid_filename, sanitize_filename
from plexapi import utils
from plexapi.exceptions import Unauthorized
from plexapi.server import PlexServer
from plexapi.utils import download

from database import add_last_run, get_last_run, add_url, check_url, add_key, check_key

SCRIPT_NAME = Path(__file__).stem

VERSION = "0.1.0"

env_file_path = Path(".env")

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

setup_logger('activity_log', ACTIVITY_LOG)
setup_logger('download_log', DOWNLOAD_LOG)

plogger(f"Starting {SCRIPT_NAME} {VERSION} at {RUNTIME_STR}", 'info', 'a')

if load_and_upgrade_env(env_file_path) < 0:
    exit()

ID_FILES = True

URL_ARRAY = []
# no one using this yet
# QUEUED_DOWNLOADS = {}

target_url_var = 'PLEX_URL'
PLEX_URL = os.getenv(target_url_var)
if PLEX_URL is None:
    target_url_var = 'PLEXAPI_AUTH_SERVER_BASEURL'
    PLEX_URL = os.getenv(target_url_var)

target_token_var = 'PLEX_TOKEN'
PLEX_TOKEN = os.getenv(target_token_var)
if PLEX_TOKEN is None:
    target_token_var = 'PLEXAPI_AUTH_SERVER_TOKEN'
    PLEX_TOKEN = os.getenv(target_token_var)

if PLEX_URL is None or PLEX_URL == 'https://plex.domain.tld':
    plogger(f"You must specify {target_url_var} in the .env file.", 'info', 'a')
    exit()

if PLEX_TOKEN is None or PLEX_TOKEN == 'PLEX-TOKEN':
    plogger(f"You must specify {target_token_var} in the .env file.", 'info', 'a')
    exit()

LIBRARY_NAME = os.getenv("LIBRARY_NAME")
LIBRARY_NAMES = os.getenv("LIBRARY_NAMES")
POSTER_DIR = os.getenv("POSTER_DIR")

SUPERCHAT = os.getenv("SUPERCHAT")

INCLUDE_COLLECTION_MEMBERS = booler(os.getenv("INCLUDE_COLLECTION_MEMBERS"))
ONLY_COLLECTION_MEMBERS = booler(os.getenv("ONLY_COLLECTION_MEMBERS"))
DELAY = int(os.getenv("DELAY"))

if not DELAY:
    DELAY = 0

if LIBRARY_NAMES:
    LIB_ARRAY = [s.strip() for s in LIBRARY_NAMES.split(",")]
else:
    LIB_ARRAY = [LIBRARY_NAME]

ONLY_THESE_COLLECTIONS = os.getenv("ONLY_THESE_COLLECTIONS")

if ONLY_THESE_COLLECTIONS:
    COLLECTION_ARRAY = [s.strip() for s in ONLY_THESE_COLLECTIONS.split("|")]
else:
    COLLECTION_ARRAY = []

imdb_str = "imdb://"
tmdb_str = "tmdb://"
tvdb_str = "tvdb://"

redaction_list = []
redaction_list.append(os.getenv('PLEXAPI_AUTH_SERVER_BASEURL'))
redaction_list.append(os.getenv('PLEXAPI_AUTH_SERVER_TOKEN'))

plex = get_plex()

logger("Plex connection succeeded", 'info', 'a')

def lib_type_supported(lib):
    return(lib.type == 'movie' or lib.type == 'show')

ALL_LIBS = plex.library.sections()
ALL_LIB_NAMES = []

logger(f"{len(ALL_LIBS)} libraries found:", 'info', 'a')
for lib in ALL_LIBS:
    logger(f"{lib.title.strip()}: {lib.type} - supported: {lib_type_supported(lib)}", 'info', 'a')
    ALL_LIB_NAMES.append(f"{lib.title.strip()}")

if LIBRARY_NAMES == 'ALL_LIBRARIES':
    LIB_ARRAY = []
    for lib in ALL_LIBS:
        if lib_type_supported(lib):
            LIB_ARRAY.append(lib.title.strip())

TOPLEVEL_TMID = ""
TOPLEVEL_TVID = ""

def get_lib_setting(the_lib, the_setting):
    settings = the_lib.settings()
    for setting in settings:
        if setting.id == the_setting:
            return setting.value

for lib in LIB_ARRAY:
    if lib in ALL_LIB_NAMES:
        try:
            highwater = 0

            plogger(f"Loading {lib} ...", 'info', 'a')
            the_lib = plex.library.section(lib)
            the_uuid = the_lib.uuid
            superchat(f"{the_lib} uuid {the_uuid}", 'info', 'a')
            ID_ARRAY = []
            the_title = the_lib.title
            superchat(f"This library is called {the_title}", 'info', 'a')

            if INCLUDE_COLLECTION_MEMBERS:
                plogger(f"getting collections from [{lib}]...", 'info', 'a')

                items = the_lib.collections()
                item_total = len(items)
                plogger(f"{item_total} collection(s) retrieved...", 'info', 'a')

                tgt_ext = ".dat"

                if item_total > 0:
                    with alive_bar(
                        item_total, dual_line=True, title="Grab Collection details"
                    ) as bar:
                        for item in items:
                            plogger(f"This collection is called {item.title}", 'info', 'a')

                            collection_items = item.items()
                            coll_item_total = len(collection_items)
                            coll_idx = 1
                            for collection_item in collection_items:
                                imdbid, tmid, tvid = get_ids(collection_item.guids, None)
                                if the_lib.TYPE == 'movie':
                                    plogger(f"Collection: {item.title} item {coll_idx : >5}/{coll_item_total : >5} | TMDb ID: {tmid : >7}    | IMDb ID: {imdbid : >10}  | {collection_item.title}", 'info', 'a')
                                else:
                                    plogger(f"Collection: {item.title} item {coll_idx : >5}/{coll_item_total : >5} | TVDb ID: {tvid : >6}    | IMDb ID: {imdbid : >10}  | {collection_item.title}", 'info', 'a')
                                coll_idx += 1
                            bar()

            else:
                plogger(f"Skipping collection members ...", 'info', 'a')

            if not ONLY_COLLECTION_MEMBERS:

                if len(COLLECTION_ARRAY) == 0:
                    COLLECTION_ARRAY = ['placeholder_collection_name']

                for coll in COLLECTION_ARRAY:
                    lib_key = f"{the_uuid}-{coll}"

                    items = []

                    if coll == 'placeholder_collection_name':
                        plogger(f"Loading {the_lib.TYPE}s  ...", 'info', 'a')
                        items = get_all_from_library(plex, the_lib, None, None)
                        plogger(f"Completed loading {len(items)} of {the_lib.totalViewSize()} {the_lib.TYPE}(s) from {the_lib.title}", 'info', 'a')

                    else:
                        plogger(f"Loading everything in collection {coll} ...", 'info', 'a')
                        items = get_all_from_library(plex, the_lib, None, {'collection': coll})
                        plogger(f"Completed loading {len(items)} from collection {coll}", 'info', 'a')

                    item_total = len(items)

                    if item_total > 0:
                        logger(f"looping over {item_total} items...", 'info', 'a')
                        item_count = 0

                        plex_links = []
                        external_links = []

                        with alive_bar(item_total, dual_line=True, title=f"Grab all posters {the_lib.title}") as bar:
                            for item in items:
                                try:
                                    imdbid, tmid, tvid = get_ids(item.guids, None)
                                    if the_lib.TYPE == 'movie':
                                        plogger(f"tem {item_count : >5}/{item_total : >5} | TMDb ID: {tmid : >7}    | IMDb ID: {imdbid : >10}  | {item.title}", 'info', 'a')
                                    else:
                                        plogger(f"item {item_count : >5}/{item_total : >5} | TVDb ID: {tvid : >6}    | IMDb ID: {imdbid : >10}  | {item.title}", 'info', 'a')

                                    item_count += 1
                                except Exception as ex:
                                    plogger(f"Problem processing {item.title}; {ex}", 'info', 'a')

                                bar()

                        plogger(f"Processed {item_count} of {item_total}", 'info', 'a')

            progress_str = "COMPLETE"
            logger(progress_str, 'info', 'a')

        except Exception as ex:
            progress_str = f"Problem processing {lib}; {ex}"
            plogger(progress_str, 'info', 'a')
    else:
        logger(f"Library {lib} not found: available libraries on this server are: {ALL_LIB_NAMES}", 'info', 'a')

plogger(f"Complete!", 'info', 'a')
