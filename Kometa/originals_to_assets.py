""" Module to transfer Kometa ioverlay backup images to asset direectory """
#!/usr/bin/env python

import os
import shutil
import sys
from datetime import datetime
from pathlib import Path, PurePath
from logs import setup_logger, plogger, logger

from alive_progress import alive_bar
from helpers import (booler, get_all_from_library, get_plex, get_se_str, validate_filename, load_and_upgrade_env)

SCRIPT_NAME = Path(__file__).stem

# 0.0.2 added superchatty logging
# 0.0.3 guardrail to prevent trying to get the seasonNumber of a show
# 0.0.4 more chatty logging and bail if the original isn't found
# 0.0.5 Actually fix TV libraries
# 0.0.6 pylint changes

VERSION = "0.0.6"

env_file_path = Path(".env")

# current dateTime
now = datetime.now()

# convert to string
RUNTIME_STR = now.strftime("%Y-%m-%d %H:%M:%S")

ACTIVITY_LOG = f"{SCRIPT_NAME}.log"
SUPERCHAT = False

def superchat(sc_msg, level, logfile):
    """docstring placeholder"""
    if SUPERCHAT:
        logger(sc_msg, level, logfile)

setup_logger('activity_log', ACTIVITY_LOG)

plogger(f"Starting {SCRIPT_NAME} {VERSION} at {RUNTIME_STR}", 'info', 'a')

if load_and_upgrade_env(env_file_path) < 0:
    sys.exit()

ID_FILES = True

TARGET_URL_VAR = 'PLEX_URL'
plex_url = os.getenv(TARGET_URL_VAR)
if plex_url is None:
    TARGET_URL_VAR = 'PLEXAPI_AUTH_SERVER_BASEURL'
    plex_url = os.getenv(TARGET_URL_VAR)

# strip a trailing slash
plex_url = plex_url.rstrip("/")

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

SUPERCHAT = os.getenv("SUPERCHAT")

ASSET_DIR_LOOKUP = {}

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

KOMETA_CONFIG_DIR = os.getenv("KOMETA_CONFIG_DIR")

redaction_list = []
redaction_list.append(os.getenv('PLEXAPI_AUTH_SERVER_BASEURL'))
redaction_list.append(os.getenv('PLEXAPI_AUTH_SERVER_TOKEN'))

plex = get_plex()

logger("Plex connection succeeded", 'info', 'a')

def lib_type_supported(tgt_lib):
    """docstring placeholder"""
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

def find_original(library_title, the_tgt_key):
    """docstring placeholder"""
    org_file = None
    # KOMETA_CONFIG_DIR=/opt/kometa/Kometa/config
    original_path = Path(KOMETA_CONFIG_DIR, 'overlays', f"{library_title} Original Posters")
    org_file = Path(original_path, f"{the_tgt_key}.jpg")

    return org_file

def target_asset(tgt_item):
    """docstring placeholder"""
    tgt_file = None
    superchat(f"getting target asset name for {tgt_item.TYPE} {tgt_item.title}", 'info', 'a')

    item_se_str = get_se_str(tgt_item)
    item_season = None
    asset_name = None

    if tgt_item.TYPE == 'movie':
        video_file = tgt_item.media[0].parts[0].file
        superchat(f"Video file: {video_file}", 'info', 'a')

        asset_name = Path(video_file).parent.stem
        superchat(f"Movie asset name: {asset_name}", 'info', 'a')

    if tgt_item.TYPE == 'show':
        locs = tgt_item.locations
        superchat(f"locations: {locs}", 'info', 'a')
        target_path = PurePath(locs[0])
        superchat(f"target_path: {target_path}", 'info', 'a')
        asset_name = target_path.name
        superchat(f"Show asset name: {asset_name}", 'info', 'a')
        ASSET_DIR_LOOKUP[tgt_item.ratingKey] = asset_name

    if tgt_item.TYPE == 'season':
        item_season = tgt_item.seasonNumber
        superchat(f"item_season: {item_season}", 'info', 'a')
        asset_name = ASSET_DIR_LOOKUP[tgt_item.parentRatingKey]
        superchat(f"Season asset name: {asset_name}", 'info', 'a')

    if tgt_item.TYPE == 'episode':
        asset_name = ASSET_DIR_LOOKUP[tgt_item.grandparentRatingKey]
        superchat(f"Episode asset name: {asset_name}", 'info', 'a')

    if USE_ASSET_FOLDERS:
        # Movie/Show poster      <path_to_assets>/ASSET_NAME/poster.ext
        tgt_file = Path(ASSET_PATH, asset_name, "poster.jpg")
        # Season poster          <path_to_assets>/ASSET_NAME/Season##.ext
        if tgt_item.TYPE == "season":
            tgt_file = Path(ASSET_PATH, asset_name, f"Season{str(item_season).zfill(2)}.jpg")
        # Episode poster         <path_to_assets>/ASSET_NAME/S##E##.ext
        if tgt_item.TYPE == "episode":
            tgt_file = Path(ASSET_PATH, asset_name, f"{item_se_str}.jpg")
    else:
        # Movie/Show poster      <path_to_assets>/ASSET_NAME.ext
        tgt_file = Path(ASSET_PATH, f"{asset_name}.jpg")
        # Season poster          <path_to_assets>/ASSET_NAME_Season##.ext
        if tgt_item.TYPE == "season":
            tgt_file = Path(ASSET_PATH, f"{asset_name}_Season{str(item_season).zfill(2)}.jpg")
        # Episode poster         <path_to_assets>/ASSET_NAME_S##E##.ext
        if tgt_item.TYPE == "episode":
            tgt_file = Path(ASSET_PATH, f"{asset_name}_{item_se_str}.jpg")

    superchat(f"Target file: {tgt_file}", 'info', 'a')

    return tgt_file

for lib in LIB_ARRAY:
    if lib in ALL_LIB_NAMES:
        try:
            HIGHWATER = 0

            plogger(f"Loading {lib} ...", 'info', 'a')
            the_lib = plex.library.section(lib)
            the_uuid = the_lib.uuid
            superchat(f"{the_lib} uuid {the_uuid}", 'info', 'a')

            the_title = the_lib.title
            superchat(f"This library is called {the_title}", 'info', 'a')
            title, msg = validate_filename(the_title)

            items = []

            plogger(f"Loading {the_lib.TYPE}s  ...", 'info', 'a')
            ITEM_COUNT, items = get_all_from_library(the_lib, None, None)
            plogger(f"Completed loading {len(items)} of {ITEM_COUNT} {the_lib.TYPE}(s) from {the_lib.title}", 'info', 'a')

            if the_lib.TYPE == "show":
                plogger("Loading seasons ...", 'info', 'a')
                season_count, seasons = get_all_from_library(the_lib, 'season', None)
                plogger(f"Completed loading {len(seasons)} of {season_count} season(s) from {the_lib.title}", 'info', 'a')
                items.extend(seasons)
                superchat(f"{len(items)} items to examine", 'info', 'a')

                plogger("Loading episodes ...", 'info', 'a')
                episode_count, episodes = get_all_from_library(the_lib, 'episode', None)
                plogger(f"Completed loading {len(episodes)} of {episode_count} episode(s) from {the_lib.title}", 'info', 'a')
                items.extend(episodes)
                superchat(f"{len(items)} items to examine", 'info', 'a')

            ITEM_TOTAL = len(items)
            if ITEM_TOTAL > 0:
                logger(f"looping over {ITEM_TOTAL} items...", 'info', 'a')
                ITEM_COUNT = 0

                plex_links = []
                external_links = []

                with alive_bar(ITEM_TOTAL, dual_line=True, title=f"Grab all posters {the_lib.title}") as bar:
                    for item in items:
                        try:
                            # get rating key
                            the_key = item.ratingKey
                            superchat(f"{item.title} key: {the_key}", 'info', 'a')

                            # find image in originals as Path
                            original_file = find_original(the_lib.title, the_key)
                            superchat(f"{item.title} original file: {original_file}", 'info', 'a')

                            if original_file.exists():
                                superchat(f"{item.title} original file is here.", 'info', 'a')

                                # get asset path as Path
                                target_file = target_asset(item)
                                superchat(f"{item.title} target file: {target_file}", 'info', 'a')

                                # create folders on the way to the target
                                target_file.parent.mkdir(parents=True, exist_ok=True)
                                superchat(f"Created folders for: {target_file}", 'info', 'a')

                                # copy original image to asset dir, overwriting whatever's there
                                shutil.copy(original_file, target_file)
                                superchat(f"copied {original_file}", 'info', 'a')
                                superchat(f"    to {target_file}", 'info', 'a')
                            else:
                                plogger(f"{item.title} ORIGINAL NOT FOUND: {original_file}", 'info', 'a')

                            ITEM_COUNT += 1
                        except Exception as ex: # pylint: disable=broad-exception-caught
                            plogger(f"Problem processing {item.title}; {ex}", 'info', 'a')

                        bar() # pylint: disable=not-callable

                plogger(f"Processed {ITEM_COUNT} of {ITEM_TOTAL}", 'info', 'a')

            logger("COMPLETE", 'info', 'a')

        except Exception as ex: # pylint: disable=broad-exception-caught
            plogger(f"Problem processing {lib}; {ex}", 'info', 'a')

    else:
        logger(f"Library {lib} not found: available libraries on this server are: {ALL_LIB_NAMES}", 'info', 'a')

plogger("Complete!", 'info', 'a')
