""" Get all the item IDs from a Plex library """
#!/usr/bin/env python
import os
import platform
import sys
from datetime import datetime
from pathlib import Path
from logs import setup_logger, plogger, logger

from alive_progress import alive_bar
from helpers import (booler, get_all_from_library, get_ids, get_plex, load_and_upgrade_env)


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
    """ Log to the console """
    if SUPERCHAT:
        logger(msg, level, logfile)

setup_logger('activity_log', ACTIVITY_LOG)
setup_logger('download_log', DOWNLOAD_LOG)

plogger(f"Starting {SCRIPT_NAME} {VERSION} at {RUNTIME_STR}", 'info', 'a')

if load_and_upgrade_env(env_file_path) < 0:
    sys.exit()

ID_FILES = True

URL_ARRAY = []
# no one using this yet
# QUEUED_DOWNLOADS = {}

TARGET_URL_VAR = 'PLEX_URL'
plex_url = os.getenv(TARGET_URL_VAR)
if plex_url is None:
    TARGET_URL_VAR = 'PLEXAPI_AUTH_SERVER_BASEURL'
    plex_url = os.getenv(TARGET_URL_VAR)

TARGET_TOKEN_VAR = 'PLEX_TOKEN'
plex_token = os.getenv(TARGET_TOKEN_VAR)
if plex_token is None:
    TARGET_TOKEN_VAR = 'PLEXAPI_AUTH_SERVER_TOKEN'
    plex_token = os.getenv(TARGET_TOKEN_VAR)

if plex_url is None or plex_url == 'https://plex.domain.tld':
    plogger(f"You must specify {TARGET_URL_VAR} in the .env file.", 'info', 'a')
    sys.exit()

if plex_token is None or plex_token == 'PLEX-TOKEN':
    plogger(f"You must specify {TARGET_TOKEN_VAR} in the .env file.", 'info', 'a')
    sys.exit()

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

IMDB_STR = "imdb://"
TMDB_STR = "tmdb://"
TVDB_STR = "tvdb://"

redaction_list = []
redaction_list.append(os.getenv('PLEXAPI_AUTH_SERVER_BASEURL'))
redaction_list.append(os.getenv('PLEXAPI_AUTH_SERVER_TOKEN'))

plex = get_plex()

logger("Plex connection succeeded", 'info', 'a')

def lib_type_supported(tgt_lib):
    """ Check if the library type is supported """
    return tgt_lib.type in ('movie', 'show')

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

def get_lib_setting(tgt_lib, the_setting): # pylint: disable=inconsistent-return-statements
    """ Get a setting from a library """
    settings = tgt_lib.settings()
    for setting in settings:
        if setting.id == the_setting:
            return setting.value

for lib in LIB_ARRAY:
    if lib in ALL_LIB_NAMES:
        try:
            HIGHWATER = 0

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

                TGT_EXT = ".dat"

                if item_total > 0:
                    with alive_bar(
                        item_total, dual_line=True, title="Grab Collection details"
                    ) as bar:
                        for item in items:
                            plogger(f"This collection is called {item.title}", 'info', 'a')

                            collection_items = item.items()
                            coll_item_total = len(collection_items)
                            COLL_IDX = 1
                            for collection_item in collection_items:
                                imdbid, tmid, tvid = get_ids(collection_item.guids)
                                if the_lib.TYPE == 'movie':
                                    plogger(f"Collection: {item.title} item {COLL_IDX : >5}/{coll_item_total : >5} | TMDb ID: {tmid : >7}    | IMDb ID: {imdbid : >10}  | {collection_item.title}", 'info', 'a') # pylint: disable=line-too-long
                                else:
                                    plogger(f"Collection: {item.title} item {COLL_IDX : >5}/{coll_item_total : >5} | TVDb ID: {tvid : >6}    | IMDb ID: {imdbid : >10}  | {collection_item.title}", 'info', 'a') # pylint: disable=line-too-long
                                COLL_IDX += 1

                            bar() # pylint: disable=not-callable

            else:
                plogger("Skipping collection members ...", 'info', 'a')

            if not ONLY_COLLECTION_MEMBERS:

                if len(COLLECTION_ARRAY) == 0:
                    COLLECTION_ARRAY = ['placeholder_collection_name']

                for coll in COLLECTION_ARRAY:
                    lib_key = f"{the_uuid}-{coll}"

                    items = []

                    if coll == 'placeholder_collection_name':
                        plogger(f"Loading {the_lib.TYPE}s  ...", 'info', 'a')
                        item_total, items = get_all_from_library(the_lib, None, None)
                        plogger(f"Completed loading {len(items)} of {the_lib.totalViewSize()} {the_lib.TYPE}(s) from {the_lib.title}", 'info', 'a')

                    else:
                        plogger(f"Loading everything in collection {coll} ...", 'info', 'a')
                        item_total, items = get_all_from_library(the_lib, None, {'collection': coll})
                        plogger(f"Completed loading {len(items)} from collection {coll}", 'info', 'a')

                    if item_total > 0:
                        logger(f"looping over {item_total} items...", 'info', 'a')
                        ITEM_COUNT = 0

                        plex_links = []
                        external_links = []

                        with alive_bar(item_total, dual_line=True, title=f"Grab all posters {the_lib.title}") as bar:
                            for item in items:
                                try:
                                    imdbid, tmid, tvid = get_ids(item.guids)
                                    IMDBID_FORMAT = f"{imdbid : >10}" if imdbid else "       N/A"
                                    TMID_FORMAT = f"{tmid : >7}" if tmid else "    N/A"
                                    TVID_FORMAT = f"{tvid : >6}" if imdbid else "   N/A"

                                    if the_lib.TYPE == 'movie':
                                        plogger(f"item {ITEM_COUNT : >5}/{item_total : >5} | TMDb ID: {TMID_FORMAT}    | IMDb ID: {IMDBID_FORMAT}  | {item.title}", 'info', 'a')
                                    else:
                                        plogger(f"item {ITEM_COUNT : >5}/{item_total : >5} | TVDb ID: {TVID_FORMAT}    | IMDb ID: {IMDBID_FORMAT}  | {item.title}", 'info', 'a')

                                    ITEM_COUNT += 1
                                except Exception as ex: # pylint: disable=broad-exception-caught
                                    plogger(f"Problem processing {item.title}; {ex}", 'info', 'a')

                                bar() # pylint: disable=not-callable

                        plogger(f"Processed {ITEM_COUNT} of {item_total}", 'info', 'a')

            logger("COMPLETE", 'info', 'a')

        except Exception as ex: # pylint: disable=broad-exception-caught
            plogger(f"Problem processing {lib}; {ex}", 'info', 'a')
    else:
        logger(f"Library {lib} not found: available libraries on this server are: {ALL_LIB_NAMES}", 'info', 'a')

plogger("Complete!", 'info', 'a')
