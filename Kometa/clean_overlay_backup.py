"""Module which moves images from a Kometa overlay backup to a Kometa asset directory."""

#!/usr/bin/env python

import os
import sys
from os import listdir
from os.path import isfile, join
from datetime import datetime
from pathlib import Path
from logs import setup_logger, plogger, blogger, logger

from alive_progress import alive_bar
from helpers import (get_all_from_library, get_plex, load_and_upgrade_env)

SCRIPT_NAME = Path(__file__).stem

VERSION = "0.1.0"

env_file_path = Path(".env")

# current dateTime
now = datetime.now()

# convert to string
RUNTIME_STR = now.strftime("%Y-%m-%d %H:%M:%S")

ACTIVITY_LOG = f"{SCRIPT_NAME}.log"

setup_logger('activity_log', ACTIVITY_LOG)

plogger(f"Starting {SCRIPT_NAME} {VERSION} at {RUNTIME_STR}", 'info', 'a')

if load_and_upgrade_env(env_file_path) < 0:
    sys.exit()

TARGET_URL_VAR = 'PLEX_URL'
plex_url = os.getenv(TARGET_URL_VAR)
if plex_url is None:
    TARGET_URL_VAR = 'PLEXAPI_AUTH_SERVER_BASEURL'
    plex_url = os.getenv(TARGET_URL_VAR)

# strip a trailing slash
plex_url = PLEX_URL.rstrip("/")

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

KOMETA_CONFIG_DIR = os.getenv("KOMETA_CONFIG_DIR")

if KOMETA_CONFIG_DIR is None:
    plogger(f"You must specify KOMETA_CONFIG_DIR in the .env file.", 'info', 'a')
    sys.exit()

DELAY = int(os.getenv("DELAY"))

if not DELAY:
    DELAY = 0

if LIBRARY_NAMES:
    LIB_ARRAY = [s.strip() for s in LIBRARY_NAMES.split(",")]
else:
    LIB_ARRAY = [LIBRARY_NAME]

redaction_list = []
redaction_list.append(os.getenv('PLEXAPI_AUTH_SERVER_BASEURL'))
redaction_list.append(os.getenv('PLEXAPI_AUTH_SERVER_TOKEN'))

plex = get_plex()

logger("Plex connection succeeded", 'info', 'a')

ALL_LIBS = plex.library.sections()
ALL_LIB_NAMES = []

logger(f"{len(ALL_LIBS)} libraries found:", 'info', 'a')
for lib in ALL_LIBS:
    logger(f"{lib.title.strip()}: {lib.type}", 'info', 'a')
    ALL_LIB_NAMES.append(f"{lib.title.strip()}")

if LIBRARY_NAMES == 'ALL_LIBRARIES':
    LIB_ARRAY = []
    for lib in ALL_LIBS:
        LIB_ARRAY.append(lib.title.strip())

def get_se_str(item):
    if item.TYPE == "season":
        ret_val = f"S{str(item.seasonNumber).zfill(2)}"
    elif item.TYPE == "episode":
        ret_val = f"S{str(item.seasonNumber).zfill(2)}E{str(item.episodeNumber).zfill(2)}"
    else:
        ret_val = f""

    return ret_val

def get_progress_string(item):
    if item.TYPE == "season":
        ret_val = f"{item.parentTitle} - {get_se_str(item)} - {item.title}"
    elif item.TYPE == "episode":
        ret_val = f"{item.grandparentTitle} - {item.parentTitle} - {get_se_str(item)} - {item.title}"
    else:
        ret_val = f"{item.title}"

    return ret_val

for lib in LIB_ARRAY:
    if lib in ALL_LIB_NAMES:
        try:
            HIGHWATER = 0

            LIBRARY_BACKUP=f"{KOMETA_CONFIG_DIR}overlays/{lib} Original Posters"

            all_backup_files = [f for f in listdir(LIBRARY_BACKUP) if isfile(join(LIBRARY_BACKUP, f))]
            backup_dict = {}
            missing_dict = {}

            for f in all_backup_files:
                rk = f.split('.')[0]
                ext = f.split('.')[1]
                backup_dict[rk]= f"{LIBRARY_BACKUP}/{rk}.{ext}"

            plogger(f"{len(backup_dict)} images in the {lib} overlay backup directory ...", 'info', 'a')

            plogger(f"Loading {lib} ...", 'info', 'a')
            the_lib = plex.library.section(lib)
            the_uuid = the_lib.uuid

            ID_ARRAY = []
            the_title = the_lib.title

            plogger(f"Loading {the_lib.TYPE}s from {lib}  ...", 'info', 'a')
            ITEM_COUNT, items = get_all_from_library(the_lib, None, None)

            plogger(f"Completed loading {len(items)} of {ITEM_COUNT} {the_lib.TYPE}(s) from {the_lib.title}", 'info', 'a')

            if the_lib.TYPE == "show":
                plogger(f"Loading seasons from {lib}  ...", 'info', 'a')
                season_count, seasons = get_all_from_library(the_lib, 'season', None)

                plogger(f"Completed loading {len(seasons)} of {season_count} season(s) from {the_lib.title}", 'info', 'a')
                items.extend(seasons)

                plogger(f"Loading episodes from {lib}  ...", 'info', 'a')
                episode_count, episodes = get_all_from_library(the_lib, 'episode', None)

                plogger(f"Completed loading {len(episodes)} of {episode_count} episode(s) from {the_lib.title}", 'info', 'a')
                items.extend(episodes)

            ITEM_TOTAL = len(items)
            if ITEM_TOTAL > 0:
                logger(f"looping over {ITEM_TOTAL} items...", 'info', 'a')
                ITEM_COUNT = 0

                with alive_bar(ITEM_TOTAL, dual_line=True, title=f"Clean Overlay Backup {the_lib.title}") as bar:
                    for item in items:
                        try:
                            rk = f"{item.ratingKey}"
                            blogger(f"Processing {item.title}; rating key {rk}", 'info', 'a', bar)
                            if rk in backup_dict:
                                blogger(f"Rating key {rk} found", 'info', 'a', bar)
                                backup_dict.pop(rk)
                            else:
                                missing_dict[rk]= f"{item.title}"
                                blogger(f"{item.title}; rating key {rk} has no backup art", 'info', 'a', bar)


                            ITEM_COUNT += 1
                        except Exception as ex:
                            plogger(f"Problem processing {item.title}; {ex}", 'info', 'a')

                        bar()

                plogger(f"Processed {ITEM_COUNT} of {ITEM_TOTAL}", 'info', 'a')

            plogger(f"{len(backup_dict)} items to delete", 'info', 'a')

            if len(backup_dict)> 0:
                delete_list = []
                with alive_bar(ITEM_TOTAL, dual_line=True, title=f"Clean Overlay Backup {the_lib.title}") as bar:
                    for rk in backup_dict:
                        target_file = backup_dict[rk]
                        p = Path(target_file)
                        blogger(f"Deleting {target_file}", 'info', 'a', bar)
                        try:
                            p.unlink()
                            delete_list.append(rk)
                        except Exception as ex:
                            plogger(f"Problem deleting {target_file}; {ex}", 'info', 'a')

                for rk in delete_list:
                    backup_dict.pop(rk)

                if len(backup_dict)> 0:
                    plogger(f"{len(backup_dict)} items could not be deleted", 'info', 'a')

            plogger(f"{len(missing_dict)} items in Plex with no backup art", 'info', 'a')
            plogger(f"These might be items added to Plex since the last overlay run", 'info', 'a')
            plogger(f"They might be items that are not intended to have overlays", 'info', 'a')

            logger("COMPLETE", 'info', 'a')

        except Exception as ex:
            plogger(f"Problem processing {lib}; {ex}", 'info', 'a')
    else:
        logger(f"Library {lib} not found: available libraries on this server are: {ALL_LIB_NAMES}", 'info', 'a')

plogger("Complete!", 'info', 'a')
