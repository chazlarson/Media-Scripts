#!/usr/bin/env python
import json
import logging
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

import filetype
import piexif
import piexif.helper
import plexapi
import requests
from alive_progress import alive_bar, alive_it
from dotenv import load_dotenv
from helpers import (booler, get_all_from_library, get_ids, get_letter_dir, get_plex,
                     get_size, redact, validate_filename, load_and_upgrade_env)
from pathvalidate import ValidationError, is_valid_filename, sanitize_filename
from plexapi import utils
from plexapi.exceptions import Unauthorized
from plexapi.server import PlexServer
from plexapi.utils import download

from database import add_last_run, get_last_run, add_media_details

# TODO: Track Collection status in SQLITE with guid
# TODO: store stuff in sqlite tables rather than text or pickle files.
# TODO: resumable queue
# TODO: only shows, seasons, episodes
# TODO: download to random number filename, rename at completion
# possible bruteforce to avoid:
# on 13983: Can't find assets/TV Shows/RuPaul's Drag Race (2009) {tvdb-85002}/S04E03-006-gracenote-remote.dat even though it was here a moment ago

# DONE 0.5.7: allowing skipping a library
# 0.5.8: QOL, bugfixes
# DONE 0.6.0: only grab new things based on a stored "last run" date
# DONE 0.6.0: store completion status at show/season/episode level

SCRIPT_NAME = Path(__file__).stem

VERSION = "0.1.0"

env_file_path = Path(".env")

# current dateTime
now = datetime.now()

# convert to string
RUNTIME_STR = now.strftime("%Y-%m-%d %H:%M:%S")

ACTIVITY_LOG = f"{SCRIPT_NAME}.log"
DOWNLOAD_LOG = f"{SCRIPT_NAME}-dl.log"
LIBRARY_STATS = f"{SCRIPT_NAME}-stats.pickle"
DOWNLOAD_QUEUE = f"{SCRIPT_NAME}-queue.pickle"

def setup_logger(logger_name, log_file, level=logging.INFO):
    log_setup = logging.getLogger(logger_name)
    formatter = logging.Formatter('%(levelname)s: %(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    fileHandler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    fileHandler.setFormatter(formatter)
    log_setup.setLevel(level)
    log_setup.addHandler(fileHandler)

def setup_dual_logger(logger_name, log_file, level=logging.INFO):
    log_setup = logging.getLogger(logger_name)
    formatter = logging.Formatter('%(levelname)s: %(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    fileHandler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    fileHandler.setFormatter(formatter)
    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(formatter)
    log_setup.setLevel(level)
    log_setup.addHandler(fileHandler)
    log_setup.addHandler(streamHandler)

def logger(msg, level, logfile):
    if logfile == 'a'   : log = logging.getLogger('activity_log')
    if logfile == 'd'   : log = logging.getLogger('download_log')
    if level == 'info'    : log.info(msg)
    if level == 'warning' : log.warning(msg)
    if level == 'error'   : log.error(msg)

def plogger(msg, level, logfile):
    if logfile == 'a'   : log = logging.getLogger('activity_log')
    if logfile == 'd'   : log = logging.getLogger('download_log')
    if level == 'info'    : log.info(msg)
    if level == 'warning' : log.warning(msg)
    if level == 'error'   : log.error(msg)
    print(msg)

def blogger(msg, level, logfile, bar):
    if logfile == 'a'   : log = logging.getLogger('activity_log')
    if logfile == 'd'   : log = logging.getLogger('download_log')
    if level == 'info'    : log.info(msg)
    if level == 'warning' : log.warning(msg)
    if level == 'error'   : log.error(msg)
    bar.text(msg)

setup_logger('activity_log', ACTIVITY_LOG)
setup_logger('download_log', DOWNLOAD_LOG)

logging.basicConfig(
    filename=f"{SCRIPT_NAME}.log",
    filemode="w",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

plogger(f"Starting {SCRIPT_NAME} {VERSION} at {RUNTIME_STR}", 'info', 'a')

if load_and_upgrade_env(env_file_path) < 0:
    exit()

lib_stats = {}

stat_file = Path(LIBRARY_STATS)

if stat_file.is_file():
    with open(stat_file, 'rb') as sf:
        lib_stats = pickle.load(sf)

queue_file = Path(DOWNLOAD_QUEUE)

# if queue_file.is_file():
#     with open(queue_file, 'rb') as qf:
#         download_queue = pickle.load(qf)

ID_FILES = True

URL_ARRAY = []
QUEUED_DOWNLOADS = {}
STATUS_FILE_NAME = "URLS.txt"
STOP_FILE_NAME = "stop.dat"
SKIP_FILE_NAME = "skip.dat"

WEEKS_BACK = 10400

fallback_date = now - timedelta(weeks = WEEKS_BACK)

LIBRARY_NAME = os.getenv("LIBRARY_NAME")
LIBRARY_NAMES = os.getenv("LIBRARY_NAMES")
POSTER_DIR = os.getenv("POSTER_DIR")

if POSTER_DIR is None:
    POSTER_DIR = 'extracted_posters'

try:
    POSTER_DEPTH = int(os.getenv("POSTER_DEPTH"))
except:
    POSTER_DEPTH = 0

POSTER_DOWNLOAD = booler(os.getenv("POSTER_DOWNLOAD"))
if not POSTER_DOWNLOAD:
    print("================== ATTENTION ==================")
    print("Downloading disabled; file identification not possible")
    print("Script will default to .jpg extension on all images")
    print("================== ATTENTION ==================")
    ID_FILES = False
POSTER_CONSOLIDATE = booler(os.getenv("POSTER_CONSOLIDATE"))
INCLUDE_COLLECTION_ARTWORK = booler(os.getenv("INCLUDE_COLLECTION_ARTWORK"))
ONLY_COLLECTION_ARTWORK = booler(os.getenv("ONLY_COLLECTION_ARTWORK"))
DELAY = int(os.getenv("DELAY"))

GRAB_BACKGROUNDS = booler(os.getenv("GRAB_BACKGROUNDS"))
GRAB_SEASONS = booler(os.getenv("GRAB_SEASONS"))
ONLY_SEASONS = booler(os.getenv("ONLY_SEASONS"))

GRAB_EPISODES = booler(os.getenv("GRAB_EPISODES"))
ONLY_EPISODES = booler(os.getenv("ONLY_EPISODES"))

ONLY_CURRENT = booler(os.getenv("ONLY_CURRENT"))

if ONLY_CURRENT:
    POSTER_DIR = os.getenv("CURRENT_POSTER_DIR")

TRACK_URLS = booler(os.getenv("TRACK_URLS"))
TRACK_COMPLETION = booler(os.getenv("TRACK_COMPLETION"))

ASSET_DIR = os.getenv("ASSET_DIR")
if ASSET_DIR is None:
    ASSET_DIR = 'assets'

ASSET_PATH = Path(ASSET_DIR)

USE_ASSET_NAMING = booler(os.getenv("USE_ASSET_NAMING"))
USE_ASSET_FOLDERS = booler(os.getenv("USE_ASSET_FOLDERS"))
ASSETS_BY_LIBRARIES = booler(os.getenv("ASSETS_BY_LIBRARIES"))
NO_FS_WARNING = booler(os.getenv("NO_FS_WARNING"))
ADD_SOURCE_EXIF_COMMENT = booler(os.getenv("ADD_SOURCE_EXIF_COMMENT"))
SRC_ARRAY = []
TRACK_IMAGE_SOURCES = booler(os.getenv("TRACK_IMAGE_SOURCES"))
IGNORE_SHRINKING_LIBRARIES = booler(os.getenv("IGNORE_SHRINKING_LIBRARIES"))

if not USE_ASSET_NAMING:
    USE_ASSET_FOLDERS = False
    ASSETS_BY_LIBRARIES = False
    USE_ASSET_SUBFOLDERS = False
    FOLDERS_ONLY = False
else:
    USE_ASSET_SUBFOLDERS = booler(os.getenv("USE_ASSET_SUBFOLDERS"))
    FOLDERS_ONLY = booler(os.getenv("FOLDERS_ONLY"))
    if FOLDERS_ONLY:
        ONLY_CURRENT = FOLDERS_ONLY
    if ASSET_DIR is None:
        ASSET_DIR = 'assets'
    if not NO_FS_WARNING:
        print("================== ATTENTION ==================")
        print("You have requested asset naming.")
        print("This requires and assumes that your media is stored")
        print("in a hierarchy like this:")
        print("└── TV Shows")
        print("  └── 9-1-1 Lone Star")
        print("      └── Season 01")
        print("          ├── S01E01.mkv")
        print("          ├── S01E02.mkv")
        print("          └── S01E03.mkv")
        print("Asset directory naming is built around an 'ASSET NAME'")
        print("which is '9-1-1 Lone Star' in the above hierarchy.")
        print("Other file hierarchies are incompatible with the")
        print("KOMETA asset naming setup at this time.")
        print("================== ATTENTION ==================")
        print("To skip this in future runs, add 'NO_FS_WARNING=1' to .env")
        print("pausing for 15 seconds...")
        time.sleep(15)


if not DELAY:
    DELAY = 0

KEEP_JUNK = booler(os.getenv("KEEP_JUNK"))

SCRIPT_FILE = "get_images.sh"
SCRIPT_SEED = f"#!/bin/bash{os.linesep}{os.linesep}# SCRIPT TO GRAB IMAGES{os.linesep}{os.linesep}"
IS_WINDOWS = platform.system() == "Windows"

if IS_WINDOWS:
    SCRIPT_FILE = "get_images.bat"
    SCRIPT_SEED = f"@echo off{os.linesep}{os.linesep}"

SCRIPT_STRING = ""

if POSTER_DOWNLOAD:
    SCRIPT_STRING = SCRIPT_SEED

RESET_LIBRARIES = os.getenv("RESET_LIBRARIES")

if RESET_LIBRARIES:
    RESET_ARRAY = [s.strip() for s in RESET_LIBRARIES.split(",")]
else:
    RESET_ARRAY = []

RESET_COLLECTIONS = os.getenv("RESET_COLLECTIONS")

if RESET_COLLECTIONS:
    RESET_COLL_ARRAY = [s.strip() for s in RESET_COLLECTIONS.split(",")]
else:
    RESET_COLL_ARRAY = []


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
redaction_list.append(PLEX_URL)
redaction_list.append(PLEX_TOKEN)

KNOWN_STATED_ASPECT_RATIOS = {}
KNOWN_CALCED_ASPECT_RATIOS = {}

plex = get_plex()

logger("connection success", 'info', 'a')

if LIBRARY_NAMES == 'ALL_LIBRARIES':
    LIB_ARRAY = []
    all_libs = plex.library.sections()
    for lib in all_libs:
        if lib.type == 'movie' or lib.type == 'show':
            LIB_ARRAY.append(lib.title.strip())

def get_asset_names(item):
    ret_val = {}
    item_file = None

    ret_val['poster'] = f"poster"
    ret_val['background'] = f"background"

    if item.TYPE == "collection":
        ASSET_NAME = item.title

        ret_val['asset'] = f"{ASSET_NAME}"
    elif item.TYPE == "movie":
        item_file = Path(item.media[0].parts[0].file)
        ASSET_NAME = item_file.parts[len(item_file.parts)-2]

        ret_val['asset'] = f"{ASSET_NAME}"
    elif item.TYPE == "show":
        item_file = Path(item.locations[0])
        ASSET_NAME = item_file.parts[len(item_file.parts)-1]

        ret_val['asset'] = f"{ASSET_NAME}"
    elif item.TYPE == "season":
        item_file = Path(item.show().locations[0])
        ASSET_NAME = item_file.parts[len(item_file.parts)-1]

        ret_val['poster'] = f"Season{str(item.seasonNumber).zfill(2)}"
        ret_val['background'] = f"{ret_val['poster']}_background"
        ret_val['asset'] = f"{ASSET_NAME}"
    elif item.TYPE == "episode":
        item_file = Path(item.media[0].parts[0].file)
        ASSET_NAME = item_file.parts[len(item_file.parts)-3]

        ret_val['poster'] = f"{get_SE_str(item)}"
        ret_val['background'] = f"{ret_val['poster']}_background"
        ret_val['asset'] = f"{ASSET_NAME}"
    else:
        # Don't support it
        ret_val['poster'] = None
        ret_val['background'] = None
        ret_val['asset'] = None

    return ret_val

def get_SE_str(item):
    if item.TYPE == "season":
        ret_val = f"S{str(item.seasonNumber).zfill(2)}"
    elif item.TYPE == "episode":
        ret_val = f"S{str(item.seasonNumber).zfill(2)}E{str(item.episodeNumber).zfill(2)}"
    else:
        ret_val = f""

    return ret_val

TOPLEVEL_TMID = ""
TOPLEVEL_TVID = ""

def get_lib_setting(the_lib, the_setting):
    settings = the_lib.settings()
    for setting in settings:
        if setting.id == the_setting:
            return setting.value

def get_subdir(item):
    global TOPLEVEL_TMID
    ret_val = ""
    se_str = get_SE_str(item)
    s_bit = se_str[:3]

    # collection-Adam-12 Collection
    # for assets we would want:
    # Adam-12 Collection

    if USE_ASSET_NAMING:
        asset_details = get_asset_names(item)
        return asset_details['asset']

    level_01 = None # 9-1-1 Lone Star-89393
    level_02 = None # S01-Season 1
    level_03 = None # S01E01-Pilot

    if item.type == 'collection':
        level_01, msg = validate_filename(f"collection-{item.title}")
    else:
        imdbid, tmid, tvid = get_ids(item.guids, None)
        if item.type == 'season':
            level_01, msg = validate_filename(f"{item.parentTitle}-{TOPLEVEL_TMID}") # show level
            safe_season_title, msg = validate_filename(item.title)
            level_02 = f"{s_bit}-{safe_season_title}"
        elif item.type == 'episode':
            level_01, msg = validate_filename(f"{item.grandparentTitle}-{TOPLEVEL_TMID}") # show level
            safe_season_title, msg = validate_filename(item.parentTitle)
            level_02 = f"{s_bit}-{safe_season_title}"
            safe_episode_title, msg = validate_filename(item.title)
            level_03 = f"{se_str}-{safe_episode_title}" # episode level
        else:
            TOPLEVEL_TMID = tmid
            TOPLEVEL_TVID = tvid
            level_01, msg = validate_filename(f"{item.title}-{TOPLEVEL_TMID}") # show level

    ret_val = Path(level_01)
    if level_02:
        ret_val = Path(ret_val, level_02)
    if level_03:
        ret_val = Path(ret_val, level_03)

    return ret_val

def get_progress_string(item):
    if item.TYPE == "season":
        ret_val = f"{item.parentTitle} - {get_SE_str(item)} - {item.title}"
    elif item.TYPE == "episode":
        ret_val = f"{item.grandparentTitle} - {item.parentTitle} - {get_SE_str(item)} - {item.title}"
    else:
        ret_val = f"{item.title}"

    return ret_val

def get_image_name(params, tgt_ext, background=False):
    ret_val = ""

    item_type = params['type']
    item_season = params['seasonNumber']
    item_se_str = params['se_str']

    idx = params['idx']
    provider = params['provider']
    source = params['source']
    safe_name, msg = validate_filename(item.title)

    if USE_ASSET_NAMING:
        if ONLY_CURRENT:
            base_name = f"{tgt_ext}"
        else:
            base_name = f"-{str(idx).zfill(3)}-{provider}-{source}{tgt_ext}"

        if background:
            ret_val = f"_background{base_name}"
        else:
            if item_type == "season":
                # _Season##.ext
                # _Season##_background.ext
                ret_val = f"_Season{str(item_season).zfill(2)}{base_name}"
            elif item_type == "episode":
                # _S##E##.ext
                # _S##E##_background.ext
                ret_val = f"_{item_se_str}{base_name}"
            else:
                if USE_ASSET_FOLDERS:
                    ret_val = f"_poster{base_name}"
                else:
                    ret_val = f"{base_name}"

    else:
        base_name = f"{str(idx).zfill(3)}-{provider}-{source}{tgt_ext}"

        if background:
            ret_val = f"background-{base_name}"
        else:
            if item_type == "season" or item_type == "episode":
                ret_val = f"{item_se_str}-{safe_name}-{base_name}"
            else:
                ret_val = f"{safe_name}-{base_name}"

    ret_val = ret_val.replace("--", "-")
    return ret_val

def check_for_images(file_path):
    jpg_path = file_path.replace(".dat", ".jpg")
    png_path = file_path.replace(".dat", ".png")

    dat_file = Path(file_path)
    jpg_file = Path(jpg_path)
    png_file = Path(png_path)

    dat_here = dat_file.is_file()
    jpg_here = jpg_file.is_file()
    png_here = png_file.is_file()

    if dat_here:
        try:
            os.remove(file_path)
        except:
            plogger(f"Can't find {file_path} even though it was here a moment ago", 'info', 'd')

    if jpg_here and png_here:
        try:
            os.remove(jpg_path)
        except:
            plogger(f"Can't find {jpg_path} even though it was here a moment ago", 'info', 'd')

        try:
            os.remove(png_path)
        except:
            plogger(f"Can't find {png_path} even though it was here a moment ago", 'info', 'd')

    if jpg_here or png_here:
        return True

    return False

executor = ThreadPoolExecutor()
my_futures = []

def process_the_thing(params):

    tmid = params['tmid']
    tvid = params['tvid']
    item_type = params['type']
    item_season = params['seasonNumber']
    item_episode = params['episodeNumber']
    item_se_str = params['se_str']

    idx = params['idx']
    folder_path = params['path']
    # current_posters/all_libraries/collection-Adam-12 Collection'
    # for assets this should be:
    # assets/One Show/Adam-12 Collection

    background = params['background']
    src_URL = params['src_URL']
    provider = params['provider']
    source = params['source']

    result = {}
    result['success'] = False
    result['status'] = 'Nothing happened'

    if not TRACK_URLS or (TRACK_URLS and URL_ARRAY.count(src_URL) == 0):
        tgt_ext = ".dat" if ID_FILES else ".jpg"
        tgt_filename = get_image_name(params, tgt_ext, background)
        # in asset case, I have '_poster.ext'

        if USE_ASSET_NAMING and not USE_ASSET_FOLDERS:
            # folder_path: assets/One Show/Adam-12 Collection
            # tgt_filename '.ext'
            # folder_path: assets/One Show/Adam-12 Collection.ext'
            # I want to take apart the path, append tgt_filename to the last element,
            # and rebuild it.
            final_file_path = str(folder_path) + tgt_filename
            bits = Path(final_file_path)
            folder_path = bits.parent
            tgt_filename = bits.name
        else:
            # folder_path: assets/One Show/Adam-12 Collection
            # tgt_filename '_poster.ext'
            # want: assets/One Show/Adam-12 Collection/poster.ext'
            # strip leading _
            if tgt_filename[0] == '_':
                tgt_filename = tgt_filename[1:]
            # then
            final_file_path = os.path.join(
                folder_path, tgt_filename
            )

        if not check_for_images(final_file_path):
            logger(f"{final_file_path} does not yet exist", 'info', 'd')
            if POSTER_DOWNLOAD:
                p = Path(folder_path)
                p.mkdir(parents=True, exist_ok=True)


                if not FOLDERS_ONLY:
                    logger(f"provider: {provider} - source: {source} - downloading {redact(src_URL, redaction_list)} to {tgt_filename}", 'info', 'd')
                    try:
                        THUMBPATH = download(
                            f"{src_URL}",
                            PLEX_TOKEN,
                            filename=tgt_filename,
                            savepath=folder_path,
                        )
                        logger(f"Downloaded {THUMBPATH}", 'info', 'd')

                        # Wait between items in case hammering the Plex server turns out badly.
                        time.sleep(DELAY)

                        local_file = str(rename_by_type(final_file_path))

                        if not KEEP_JUNK:
                            if local_file.find('.del') > 0:
                                os.remove(local_file)

                        if ADD_SOURCE_EXIF_COMMENT:
                            exif_tag = 'plex internal'

                            if source == 'remote':
                                exif_tag = src_URL

                            # Write out exif data
                            # load existing exif data from ima7ge
                            exif_dict = piexif.load(local_file)
                            # insert custom data in usercomment field
                            exif_dict["Exif"][piexif.ExifIFD.UserComment] = piexif.helper.UserComment.dump(
                                exif_tag,
                                encoding="unicode"
                            )
                            # insert mutated data (serialised into JSON) into image
                            piexif.insert(
                                piexif.dump(exif_dict),
                                local_file
                            )

                        URL_ARRAY.append(src_URL)

                        with open(URL_FILE_NAME, "a", encoding="utf-8") as sf:
                            sf.write(f"{src_URL}{os.linesep}")

                        if TRACK_IMAGE_SOURCES:
                            with open(SOURCE_FILE_NAME, "a", encoding="utf-8") as sf:
                                sf.write(f"{local_file} - {redact(src_URL, redaction_list)}{os.linesep}")

                    except Exception as ex:
                        result['success'] = False
                        result['status'] = f"{ex}"
                        logger(f"error on {src_URL} - {ex}", 'info', 'd')
            else:
                mkdir_flag = "" if IS_WINDOWS else "-p "
                script_line_start = ""
                if idx == 1:
                    script_line_start = f'mkdir {mkdir_flag}"{folder_path}"{os.linesep}'

                script_line = f'{script_line_start}curl -C - -fLo "{os.path.join(folder_path, tgt_filename)}" "{src_URL}"'

                SCRIPT_STRING = (
                    SCRIPT_STRING + f"{script_line}{os.linesep}"
                )
    else:
        result['success'] = True
        result['status'] = 'duplicate URL'

    return result

class poster_placeholder:
    def __init__(self, provider, key):
        self.provider = provider
        self.key = key

def get_art(item, artwork_path, tmid, tvid):
    global SCRIPT_STRING
    attempts = 0
    if ONLY_CURRENT:
        all_art = []
        all_art.append(poster_placeholder('current', item.art))
    else:
        all_art = item.arts()

    if USE_ASSET_NAMING:
        bg_path = artwork_path
    else:
        bg_path = Path(artwork_path, "backgrounds")

    while attempts < 5:
        try:
            progress_str = f"{get_progress_string(item)} - {len(all_art)} backgrounds"

            blogger(progress_str, 'info', 'a', bar)

            import fnmatch

            if ONLY_CURRENT:
                no_point_in_looking = False
            else:
                count = 0
                posters_to_go = 0

                if os.path.exists(bg_path):
                    # if I'm using asset naming, the names all start with `background``
                    if USE_ASSET_NAMING:
                        count = len(fnmatch.filter(os.listdir(bg_path), "background*.*"))
                    else:
                        count = len(fnmatch.filter(os.listdir(bg_path), "*.*"))
                    logger(f"{count} files in {bg_path}", 'info', 'a')

                posters_to_go = count - POSTER_DEPTH

                if posters_to_go < 0:
                    poster_to_go = abs(posters_to_go)
                else:
                    poster_to_go = 0

                logger(f"{poster_to_go} needed to reach depth {POSTER_DEPTH}", 'info', 'a')

                no_more_to_get = count >= len(all_art)
                full_for_now = count >= POSTER_DEPTH and POSTER_DEPTH > 0
                no_point_in_looking = full_for_now or no_more_to_get
                if no_more_to_get:
                    logger(f"Grabbed all available posters: {no_more_to_get}", 'info', 'a')
                if full_for_now:
                    logger(f"full_for_now: {full_for_now} - {POSTER_DEPTH} image(s) retrieved already", 'info', 'a')

            if not no_point_in_looking:
                idx = 1
                for art in all_art:
                    if art.key is not None:
                        if POSTER_DEPTH > 0 and idx > POSTER_DEPTH:
                            logger(f"Reached max depth of {POSTER_DEPTH}; exiting loop", 'info', 'a')
                            break

                        art_params = {}
                        art_params['tmid'] = tmid
                        art_params['tvid'] = tvid
                        art_params['idx'] = idx
                        art_params['path'] = bg_path
                        art_params['provider'] = art.provider
                        art_params['source'] = 'remote'

                        art_params['type'] = item.TYPE

                        try:
                            art_params['seasonNumber'] = item.seasonNumber
                        except:
                            art_params['seasonNumber'] = None

                        try:
                            art_params['episodeNumber'] = item.episodeNumber
                        except:
                            art_params['episodeNumber'] = None

                        art_params['se_str'] = get_SE_str(item)

                        art_params['background'] = True

                        src_URL = art.key
                        if src_URL[0] == "/":
                            src_URL = f"{PLEX_URL}{art.key}&X-Plex-Token={PLEX_TOKEN}"
                            art_params['source'] = 'local'

                        art_params['src_URL'] = src_URL

                        bar.text = f"{progress_str} - {idx}"
                        logger(f"processing {progress_str} - {idx}", 'info', 'a')

                        future = executor.submit(process_the_thing, art_params) # does not block
                        # append it to the queue
                        my_futures.append(future)

                    else:
                        logger(f"skipping empty internal art object", 'info', 'a')

                    idx += 1

            attempts = 6
        except Exception as ex:
            progress_str = f"EX: {ex} {item.title}"
            logger(progress_str, 'info', 'a')
            attempts  += 1

def get_posters(lib, item):
    global SCRIPT_STRING

    imdbid = None
    tmid = None
    tvid = None

    collection_title = None
    movie_title = None
    show_title = None
    season_title = None
    episode_title = None

    if item.type != 'collection':
        imdbid, tmid, tvid = get_ids(item.guids, None)
        if item.type == "show":
            show_title = item.title
        if item.type == "movie":
            movie_title = item.title
        if item.type == "season":
            show_title = item.parentTitle
            season_title = item.title
        if item.type == "episode":
            show_title = item.grandparentTitle
            season_title = item.parentTitle
            episode_title = item.title
    else:
        collection_title = item.title

    if USE_ASSET_NAMING:
        tgt_dir = ASSET_DIR
        if ASSETS_BY_LIBRARIES:
            tgt_dir = os.path.join(tgt_dir, lib)
    else:
        if POSTER_CONSOLIDATE:
            tgt_dir = os.path.join(POSTER_DIR, "all_libraries")
        else:
            tgt_dir = os.path.join(POSTER_DIR, lib)
    # current_posters/all_libraries
    # for assets we want:
    # assets/One Show

    # add a letter level here.
    if USE_ASSET_SUBFOLDERS:
        if item.type == 'collection':
            tgt_dir = os.path.join(tgt_dir, "Collections")
        else:
            # TODO: This is broken as it doesn't account for The in season/episode cases
            asset_subdir_target = item.titleSort
            if item.type == "season" or item.type == "episode":
                asset_subdir_target = show_title
            tgt_dir = os.path.join(tgt_dir, get_letter_dir(asset_subdir_target))

    if not os.path.exists(tgt_dir):
        os.makedirs(tgt_dir)

    attempts = 0

    item_path= get_subdir(item)
    # collection-Adam-12 Collection
    # for assets we would want:
    # Adam-12 Collection
    artwork_path = Path(tgt_dir, item_path)
    logger(f"final artwork_path: {artwork_path}", 'info', 'a')
    # current_posters/all_libraries/collection-Adam-12 Collection'
    # for assets this should be:
    # assets/One Show/Adam-12 Collection

    attempts = 0
    if ONLY_CURRENT:
        all_posters = []
        all_posters.append(poster_placeholder('current', item.thumb))
    else:
        all_posters = item.posters()

    while attempts < 5:
        try:
            progress_str = f"{get_progress_string(item)} - {len(all_posters)} posters"

            blogger(progress_str, 'info', 'a', bar)

            import fnmatch

            if ONLY_CURRENT:
                no_point_in_looking = False
            else:
                count = 0
                posters_to_go = 0

                search_filter = "*.*"
                if item.type == "season":
                    search_filter = f"Season{str(item.seasonNumber).zfill(2)}*.*"
                if item.type == "episode":
                    search_filter = f"{get_SE_str(item)}*.*"

                if os.path.exists(artwork_path):
                    logger(f"{artwork_path} exists", 'info', 'a')
                    count = len(fnmatch.filter(os.listdir(artwork_path), search_filter))
                    logger(f"{count} files in {artwork_path}", 'info', 'a')

                posters_to_go = count - POSTER_DEPTH

                if posters_to_go < 0:
                    poster_to_go = abs(posters_to_go)
                else:
                    poster_to_go = 0

                logger(f"{poster_to_go} needed to reach depth {POSTER_DEPTH}", 'info', 'a')

                no_more_to_get = count >= len(all_posters)
                full_for_now = count >= POSTER_DEPTH and POSTER_DEPTH > 0
                no_point_in_looking = full_for_now or no_more_to_get
                if no_more_to_get:
                    logger(f"Grabbed all available posters: {no_more_to_get}", 'info', 'a')
                if full_for_now:
                    logger(f"full_for_now: {full_for_now} - {POSTER_DEPTH} image(s) retrieved already", 'info', 'a')

            if not no_point_in_looking:
                idx = 1
                for poster in all_posters:
                    if POSTER_DEPTH > 0 and idx > POSTER_DEPTH:
                        logger(f"Reached max depth of {POSTER_DEPTH}; exiting loop", 'info', 'a')
                        break

                    art_params = {}
                    art_params['rating_key'] = item.ratingKey
                    art_params['tmid'] = tmid
                    art_params['tvid'] = tvid
                    # art_params['item'] = item
                    art_params['idx'] = idx
                    art_params['path'] = artwork_path
                    art_params['provider'] = poster.provider
                    art_params['source'] = 'remote'

                    art_params['type'] = item.TYPE

                    try:
                        art_params['seasonNumber'] = item.seasonNumber
                    except:
                        art_params['seasonNumber'] = None

                    try:
                        art_params['episodeNumber'] = item.episodeNumber
                    except:
                        art_params['episodeNumber'] = None

                    art_params['se_str'] = get_SE_str(item)

                    art_params['background'] = False

                    src_URL = poster.key

                    if src_URL[0] == "/":
                        src_URL = f"{PLEX_URL}{poster.key}&X-Plex-Token={PLEX_TOKEN}"
                        art_params['source'] = 'local'

                    art_params['src_URL'] = src_URL

                    bar.text = f"{progress_str} - {idx}"
                    logger(f"processing {progress_str} - {idx}", 'info', 'a')

                    future = executor.submit(process_the_thing, art_params) # does not block
                    my_futures.append(future)
                    # process_the_thing(art_params)
                    QUEUED_DOWNLOADS[item.ratingKey] = art_params
                    # this key cant be just the ratingkey; has to be ratingkey-idx-background?

                    with open(queue_file, 'wb') as qf:
                        pickle.dump(QUEUED_DOWNLOADS, qf)

                    idx += 1

            attempts = 6
        except Exception as ex:
            progress_str = f"EX: {ex} {item.title}"
            logger(progress_str, 'info', 'a')

            attempts  += 1

    if GRAB_BACKGROUNDS:
        get_art(item, artwork_path, tmid, tvid)

def rename_by_type(target):
    p = Path(target)

    kind = filetype.guess(target)
    if kind is None:
        with open(target, 'r') as file:
            content = file.read()
	    	# check if string present or not
            if '404 Not Found' in content:
                logger('Contains 404, deleting', 'info', 'a')
                extension = ".del"
            else:
                logger('Cannot guess file type; using txt', 'info', 'a')
                extension = ".txt"
    else:
        extension = f".{kind.extension}"

    new_name = p.with_suffix(extension)

    if "html" in extension:
        logging.info(f"deleting html file {p}")
        p.unlink()
    else:
        logging.info(f"changing file extension to {extension} on {p}")
        p.rename(new_name)

    return new_name

def add_script_line(artwork_path, poster_file_path, src_URL_with_token):
    if IS_WINDOWS:
        script_line = f'{os.linesep}mkdir "{artwork_path}"{os.linesep}curl -C - -fLo "{Path(artwork_path, poster_file_path)}" {src_URL_with_token}'
    else:
        script_line = f'{os.linesep}mkdir -p "{artwork_path}" && curl -C - -fLo "{Path(artwork_path, poster_file_path)}" {src_URL_with_token}'
    return f"{script_line}{os.linesep}"

for lib in LIB_ARRAY:
    try:
        highwater = 0
        # start_queue_length = len(my_futures)

        # if len(my_futures) > 0:
        #     plogger(f"queue length: {len(my_futures)}", 'info', 'a')

        plogger(f"Loading {lib} ...", 'info', 'a')
        the_lib = plex.library.section(lib)
        the_uuid = the_lib.uuid

        last_run_lib = fallback_date

        ID_ARRAY = []
        the_title = the_lib.title
        # title, msg = validate_filename(the_title)
        # status_file_name = f"ratingkeys-{title}-{the_uuid}-{POSTER_DEPTH}.txt"
        # status_file = Path(status_file_name)

        # if TRACK_COMPLETION:
        #     if status_file.is_file():
        #         with open(status_file) as fp:
        #             for line in fp:
        #                 ID_ARRAY.append(line.strip())
        #             logger(f"{len(ID_ARRAY)} completed rating keys loaded", 'info', 'a')

        #         # Stick a date in the file to help with failed runs
        #         with open(status_file, "a", encoding="utf-8") as sf:
        #             sf.write(f"{RUNTIME_STR}{os.linesep}")

        # URL_ARRAY = []
        # URL_FILE_NAME = f"urls-{title}-{the_uuid}.txt"
        # url_file = Path(URL_FILE_NAME)

        # if url_file.is_file():
        #     logger(f"Reading URLs from {url_file.resolve()}", 'info', 'a')
        #     with open(url_file) as fp:
        #         for line in fp:
        #             URL_ARRAY.append(line.strip())
        #         logger(f"{len(URL_ARRAY)} URls loaded", 'info', 'a')

        # SOURCE_FILE_NAME = f"sources-{title}-{the_uuid}.txt"

        lib_key = f"{the_uuid}-aspect"

        items = []

        plogger(f"Loading {the_lib.TYPE}s new since {last_run_lib} ...", 'info', 'a')
        if the_lib.TYPE == "movie":
            items = get_all_from_library(plex, the_lib, None, {"addedAt>>": last_run_lib})
            last_run_lib = datetime.now()

        if the_lib.TYPE == "show":
            last_run_episode = fallback_date

            plogger(f"Loading episodes new since {last_run_episode} ...", 'info', 'a')
            episodes = get_all_from_library(plex, the_lib, 'episode', {"addedAt>>": last_run_episode})
            last_run_episode = datetime.now()
            items.extend(episodes)

        item_total = len(items)
        if item_total > 0:
            logger(f"looping over {item_total} items...", 'info', 'a')
            item_count = 0

            plex_links = []
            external_links = []

            with alive_bar(item_total, dual_line=True, title=f"Grab all posters {the_lib.title}") as bar:
                for item in items:
                    try:
                        if ID_ARRAY.count(f"{item.ratingKey}") == 0:
                            blogger(f"Starting {item.TYPE}: {item.title}", 'info', 'a', bar)

                            mediaParts = item.media

                            for part in mediaParts:
                                try:
                                    arc = str(round(part.width/part.height, 2))
                                except:
                                    arc = "None"
                                add_media_details(part.parts[0].file, item.title, the_lib.TYPE, part.height, part.width, part.aspectRatio, arc)

                        else:
                            blogger(f"SKIPPING {item.title}; status complete", 'info', 'a', bar)

                        item_count += 1
                    except Exception as ex:
                        plogger(f"Problem processing {item.title}; {ex}", 'info', 'a')

                    bar()

                    stop_file = Path(STOP_FILE_NAME)
                    skip_file = Path(SKIP_FILE_NAME)

                    if stop_file.is_file() or skip_file.is_file():
                        raise StopIteration

            plogger(f"Processed {item_count} of {item_total}", 'info', 'a')
            lib_stats[lib_key] = item_count

        progress_str = "COMPLETE"
        logger(progress_str, 'info', 'a')

    except StopIteration:
        if stop_file.is_file():
            progress_str = f"stop file found, leaving loop"
        if skip_file.is_file():
            progress_str = f"skip file found, skipping library"

        plogger(progress_str, 'info', 'a')

        if stop_file.is_file():
            stop_file.unlink()
            break
        if skip_file.is_file():
            skip_file.unlink()

    except Exception as ex:
        progress_str = f"Problem processing {lib}; {ex}"
        plogger(progress_str, 'info', 'a')

plogger(f"Complete!", 'info', 'a')
# shutdown the thread pool
executor.shutdown() # blocks
