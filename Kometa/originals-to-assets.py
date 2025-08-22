#!/usr/bin/env python

import shutil
from datetime import datetime
from pathlib import Path, PurePath

from alive_progress import alive_bar
from config import Config
from helpers import (get_all_from_library, get_plex, get_redaction_list,
                     get_target_libraries, validate_filename)
from logs import logger, plogger, setup_logger

config = Config('../config.yaml')

SCRIPT_NAME = Path(__file__).stem

# 0.0.2 added superchatty logging
# 0.0.3 guardrail to prevent trying to get the seasonNumber of a show
# 0.0.4 more chatty logging and bail if the original isn't found
# 0.0.5 Actually fix TV libraries
# 0.0.6 use parent directory name rather than stem

VERSION = "0.0.6"

# current dateTime
now = datetime.now()

# convert to string
RUNTIME_STR = now.strftime("%Y-%m-%d %H:%M:%S")

ACTIVITY_LOG = f"{SCRIPT_NAME}.log"
SUPERCHAT = config.get_bool("general.superchat", False)

def superchat(msg, level, logfile):
    if SUPERCHAT:
        logger(msg, level, logfile)

setup_logger("activity_log", ACTIVITY_LOG)

plogger(f"Starting {SCRIPT_NAME} {VERSION} at {RUNTIME_STR}", "info", "a")

ID_FILES = True

ASSET_DIR_LOOKUP = {}

ASSET_DIR = config.get("image_download.where_to_put_it.asset_dir", "assets")

ASSET_PATH = Path(ASSET_DIR)

USE_ASSET_FOLDERS = config.get_bool("image_download.where_to_put_it.use_asset_folders", False)

KOMETA_CONFIG_DIR = config.get("general.kometa_config_dir", "/opt/kometa/config")

redaction_list = get_redaction_list()

plex = get_plex()

LIB_ARRAY = get_target_libraries(plex)

def lib_type_supported(lib):
    return lib.type == "movie" or lib.type == "show"


def get_SE_str(item):
    superchat(f"entering get_SE_str for {item.TYPE} {item.title}", "info", "a")
    if item.TYPE == "season":
        ret_val = f"S{str(item.seasonNumber).zfill(2)}"
    elif item.TYPE == "episode":
        ret_val = (
            f"S{str(item.seasonNumber).zfill(2)}E{str(item.episodeNumber).zfill(2)}"
        )
    else:
        ret_val = ""

    superchat(f"returning {ret_val}", "info", "a")
    return ret_val


def find_original(library_title, the_key):
    original_file = None
    # KOMETA_CONFIG_DIR=/opt/kometa/Kometa/config
    original_path = Path(
        KOMETA_CONFIG_DIR, "overlays", f"{library_title} Original Posters"
    )
    original_file = Path(original_path, f"{the_key}.jpg")

    return original_file


def target_asset(item):
    target_file = None
    superchat(f"getting target asset name for {item.TYPE} {item.title}", "info", "a")

    item_se_str = get_SE_str(item)
    item_season = None
    asset_name = None

    if item.TYPE == "movie":
        video_file = item.media[0].parts[0].file
        superchat(f"Video file: {video_file}", "info", "a")

        asset_name = Path(video_file).parent.name
        superchat(f"Movie asset name: {asset_name}", "info", "a")

    if item.TYPE == "show":
        locs = item.locations
        superchat(f"locations: {locs}", "info", "a")
        target_path = PurePath(locs[0])
        superchat(f"target_path: {target_path}", "info", "a")
        asset_name = target_path.name
        superchat(f"Show asset name: {asset_name}", "info", "a")
        ASSET_DIR_LOOKUP[item.ratingKey] = asset_name

    if item.TYPE == "season":
        item_season = item.seasonNumber
        superchat(f"item_season: {item_season}", "info", "a")
        asset_name = ASSET_DIR_LOOKUP[item.parentRatingKey]
        superchat(f"Season asset name: {asset_name}", "info", "a")

    if item.TYPE == "episode":
        asset_name = ASSET_DIR_LOOKUP[item.grandparentRatingKey]
        superchat(f"Episode asset name: {asset_name}", "info", "a")

    if USE_ASSET_FOLDERS:
        # Movie/Show poster      <path_to_assets>/ASSET_NAME/poster.ext
        target_file = Path(ASSET_PATH, asset_name, "poster.jpg")
        # Season poster          <path_to_assets>/ASSET_NAME/Season##.ext
        if item.TYPE == "season":
            target_file = Path(
                ASSET_PATH, asset_name, f"Season{str(item_season).zfill(2)}.jpg"
            )
        # Episode poster         <path_to_assets>/ASSET_NAME/S##E##.ext
        if item.TYPE == "episode":
            target_file = Path(ASSET_PATH, asset_name, f"{item_se_str}.jpg")
    else:
        # Movie/Show poster      <path_to_assets>/ASSET_NAME.ext
        target_file = Path(ASSET_PATH, f"{asset_name}.jpg")
        # Season poster          <path_to_assets>/ASSET_NAME_Season##.ext
        if item.TYPE == "season":
            target_file = Path(
                ASSET_PATH, f"{asset_name}_Season{str(item_season).zfill(2)}.jpg"
            )
        # Episode poster         <path_to_assets>/ASSET_NAME_S##E##.ext
        if item.TYPE == "episode":
            target_file = Path(ASSET_PATH, f"{asset_name}_{item_se_str}.jpg")

    superchat(f"Target file: {target_file}", "info", "a")

    return target_file


for lib in LIB_ARRAY:
    try:
        highwater = 0

        plogger(f"Loading {lib} ...", "info", "a")
        the_lib = plex.library.section(lib)
        the_uuid = the_lib.uuid
        superchat(f"{the_lib} uuid {the_uuid}", "info", "a")

        the_title = the_lib.title
        superchat(f"This library is called {the_title}", "info", "a")
        title, msg = validate_filename(the_title)

        items = []

        plogger(f"Loading {the_lib.TYPE}s  ...", "info", "a")
        item_count, items = get_all_from_library(the_lib, None, None)
        plogger(
            f"Completed loading {len(items)} of {item_count} {the_lib.TYPE}(s) from {the_lib.title}",
            "info",
            "a",
        )

        if the_lib.TYPE == "show":
            plogger("Loading seasons ...", "info", "a")
            season_count, seasons = get_all_from_library(the_lib, "season", None)
            plogger(
                f"Completed loading {len(seasons)} of {season_count} season(s) from {the_lib.title}",
                "info",
                "a",
            )
            items.extend(seasons)
            superchat(f"{len(items)} items to examine", "info", "a")

            plogger("Loading episodes ...", "info", "a")
            episode_count, episodes = get_all_from_library(the_lib, "episode", None)
            plogger(
                f"Completed loading {len(episodes)} of {episode_count} episode(s) from {the_lib.title}",
                "info",
                "a",
            )
            items.extend(episodes)
            superchat(f"{len(items)} items to examine", "info", "a")

        item_total = len(items)
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
                        # get rating key
                        the_key = item.ratingKey
                        superchat(f"{item.title} key: {the_key}", "info", "a")

                        # find image in originals as Path
                        original_file = find_original(the_lib.title, the_key)
                        superchat(
                            f"{item.title} original file: {original_file}",
                            "info",
                            "a",
                        )

                        if original_file.exists():
                            superchat(
                                f"{item.title} original file is here.", "info", "a"
                            )

                            # get asset path as Path
                            target_file = target_asset(item)
                            superchat(
                                f"{item.title} target file: {target_file}",
                                "info",
                                "a",
                            )

                            # create folders on the way to the target
                            target_file.parent.mkdir(parents=True, exist_ok=True)
                            superchat(
                                f"Created folders for: {target_file}", "info", "a"
                            )

                            # copy original image to asset dir, overwriting whatever's there
                            shutil.copy(original_file, target_file)
                            superchat(f"copied {original_file}", "info", "a")
                            superchat(f"    to {target_file}", "info", "a")
                        else:
                            plogger(
                                f"{item.title} ORIGINAL NOT FOUND: {original_file}",
                                "info",
                                "a",
                            )

                        item_count += 1
                    except Exception as ex:
                        plogger(
                            f"Problem processing {item.title}; {ex}", "info", "a"
                        )

                    bar()

            plogger(f"Processed {item_count} of {item_total}", "info", "a")

        progress_str = "COMPLETE"
        logger(progress_str, "info", "a")

    except Exception as ex:
        progress_str = f"Problem processing {lib}; {ex}"
        plogger(progress_str, "info", "a")


plogger("Complete!", "info", "a")
