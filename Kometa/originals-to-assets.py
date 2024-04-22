#!/usr/bin/env python

import os
import shutil
from datetime import datetime
from pathlib import Path
from logs import setup_logger, plogger, logger

from alive_progress import alive_bar
from helpers import (booler, get_all_from_library, get_plex, validate_filename, load_and_upgrade_env)

SCRIPT_NAME = Path(__file__).stem

VERSION = "0.0.1"

env_file_path = Path(".env")

# current dateTime
now = datetime.now()

# convert to string
RUNTIME_STR = now.strftime("%Y-%m-%d %H:%M:%S")

ACTIVITY_LOG = f"{SCRIPT_NAME}.log"
SUPERCHAT = False

def superchat(msg, level, logfile):
    if SUPERCHAT:
        logger(msg, level, logfile)

setup_logger('activity_log', ACTIVITY_LOG)

plogger(f"Starting {SCRIPT_NAME} {VERSION} at {RUNTIME_STR}", 'info', 'a')

if load_and_upgrade_env(env_file_path) < 0:
    exit()

ID_FILES = True

target_url_var = 'PLEX_URL'
PLEX_URL = os.getenv(target_url_var)
if PLEX_URL is None:
    target_url_var = 'PLEXAPI_AUTH_SERVER_BASEURL'
    PLEX_URL = os.getenv(target_url_var)

# strip a trailing slash
PLEX_URL = PLEX_URL.rstrip("/")

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

SUPERCHAT = os.getenv("SUPERCHAT")

ASSET_DIR = os.getenv("ASSET_DIR")
if ASSET_DIR is None:
    ASSET_DIR = 'assets'

ASSET_PATH = Path(ASSET_DIR)

USE_ASSET_FOLDERS = booler(os.getenv("USE_ASSET_FOLDERS"))

if ASSET_DIR is None:
    ASSET_DIR = 'assets'

if LIBRARY_NAMES:
    LIB_ARRAY = [s.strip() for s in LIBRARY_NAMES.split(",")]
else:
    LIB_ARRAY = [LIBRARY_NAME]

PMM_CONFIG_DIR = os.getenv("PMM_CONFIG_DIR")

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

def get_SE_str(item):
    superchat(f"entering get_SE_str {item}", 'info', 'a')
    if item.TYPE == "season":
        ret_val = f"S{str(item.seasonNumber).zfill(2)}"
    elif item.TYPE == "episode":
        ret_val = f"S{str(item.seasonNumber).zfill(2)}E{str(item.episodeNumber).zfill(2)}"
    else:
        ret_val = f""

    superchat(f"returning {ret_val}", 'info', 'a')
    return ret_val

def find_original(library_title, the_key): 
    original_file = None
    # PMM_CONFIG_DIR=/opt/pmm/Plex-Meta-Manager/config
    original_path = Path(PMM_CONFIG_DIR, 'overlays', f"{library_title} Original Posters")
    original_file = Path(original_path, f"{the_key}.jpg")

    return original_file

def target_asset(item):
    target_file = None

    item_se_str = get_SE_str(item)
    item_season = None
    if item.TYPE != 'movie':
        item_season = item.seasonNumber
 
    asset_name = None
    try:
        video_file = item.media[0].parts[0].file
        asset_name = Path(item.media[0].parts[0].file).parent.stem
    except:
        raise FileNotFoundError

    # will only be 'poster'
    base_name = "poster.jpg"
    if USE_ASSET_FOLDERS:
        # Movie/Show poster      <path_to_assets>/ASSET_NAME/poster.ext
        target_file = Path(ASSET_PATH, asset_name, base_name)
        # Season poster          <path_to_assets>/ASSET_NAME/Season##.ext
        if item.TYPE == "season":
            target_file = Path(ASSET_PATH, asset_name, f"Season{str(item_season).zfill(2)}.jpg")
        # Episode poster         <path_to_assets>/ASSET_NAME/S##E##.ext
        if item.TYPE == "episode":
            target_file = Path(ASSET_PATH, asset_name, f"{item_se_str}{base_name}")
    else:
        # Movie/Show poster      <path_to_assets>/ASSET_NAME.ext
        target_file = Path(ASSET_PATH, f"{asset_name}.jpg")
        # Season poster          <path_to_assets>/ASSET_NAME_Season##.ext
        if item.TYPE == "season":
            target_file = Path(ASSET_PATH, f"{asset_name}_Season{str(item_season).zfill(2)}.jpg")
        # Episode poster         <path_to_assets>/ASSET_NAME_S##E##.ext
        if item.TYPE == "episode":
            target_file = Path(ASSET_PATH, f"{asset_name}_{item_se_str}{base_name}")

    return target_file
    
for lib in LIB_ARRAY:
    if lib in ALL_LIB_NAMES:
        try:
            highwater = 0

            plogger(f"Loading {lib} ...", 'info', 'a')
            the_lib = plex.library.section(lib)
            the_uuid = the_lib.uuid
            superchat(f"{the_lib} uuid {the_uuid}", 'info', 'a')

            the_title = the_lib.title
            superchat(f"This library is called {the_title}", 'info', 'a')
            title, msg = validate_filename(the_title)

            items = []

            plogger(f"Loading {the_lib.TYPE}s  ...", 'info', 'a')
            item_count, items = get_all_from_library(the_lib, None, None)
            plogger(f"Completed loading {len(items)} of {item_count} {the_lib.TYPE}(s) from {the_lib.title}", 'info', 'a')

            if the_lib.TYPE == "show":
                plogger(f"Loading seasons ...", 'info', 'a')
                season_count, seasons = get_all_from_library(the_lib, 'season', None)
                plogger(f"Completed loading {len(seasons)} of {season_count} season(s) from {the_lib.title}", 'info', 'a')
                items.extend(seasons)
                superchat(f"{len(items)} items to examine", 'info', 'a')

                plogger(f"Loading episodes ...", 'info', 'a')
                episode_count, episodes = get_all_from_library(the_lib, 'episode', None)
                plogger(f"Completed loading {len(episodes)} of {episode_count} episode(s) from {the_lib.title}", 'info', 'a')
                items.extend(episodes)
                superchat(f"{len(items)} items to examine", 'info', 'a')

            item_total = len(items)
            if item_total > 0:
                logger(f"looping over {item_total} items...", 'info', 'a')
                item_count = 0

                plex_links = []
                external_links = []

                with alive_bar(item_total, dual_line=True, title=f"Grab all posters {the_lib.title}") as bar:
                    for item in items:
                        try:
                            # get rating key
                            the_key = item.ratingKey
                            
                            # find image in originals as Path
                            original_file = find_original(the_lib.title, the_key)

                            # get asset path as Path
                            target_file = target_asset(item)

                            # create folders on the way to the target
                            target_file.parent.mkdir(parents=True, exist_ok=True)

                            # copy original image to asset dir, overwriting whatever's there
                            shutil.copy(original_file, target_file)

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
