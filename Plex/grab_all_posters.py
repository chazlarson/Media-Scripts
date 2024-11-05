""" Grab all the posters from a Plex server """
# pylint: disable=too-many-lines, fixme, too-many-nested-blocks, too-many-branches, too-many-statements, too-many-locals, global-statement
# #!/usr/bin/env python

import os
import platform
import sys
import time
import fnmatch

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path
from logs import setup_logger, plogger, blogger, logger

import filetype
from alive_progress import alive_bar
from helpers import (booler, get_all_from_library, get_ids, get_letter_dir, get_plex, get_se_str, has_overlay, redact, validate_filename, load_and_upgrade_env, check_for_images)
from pathvalidate import sanitize_filename
from plexapi.utils import download

from database import add_last_run, get_last_run, add_url, check_url, add_key, check_key

# TODO: lib_stats[lib_key] = item_count in sqlite
# TODO: Track Collection status in sqlite with guid
# ~~I can't recall what that ^ means~~ OH Track collection completion like other things using the collection's GUID
# TODO: resumable queue
# TODO: only shows, seasons, episodes
# TODO: download to random number filename, rename at completion
# possible bruteforce to avoid:
# on 13983: Can't find assets/TV Shows/RuPaul's Drag Race (2009) {tvdb-85002}/S04E03-006-gracenote-remote.dat even though it was here a moment ago
# TODO: go dig around in the overlay backup folder to find the non-overlaid art

# DONE 0.5.7: allowing skipping a library
# 0.5.8: QOL, bugfixes
# DONE 0.6.0: only grab new things based on a stored "last run" date
# DONE 0.6.0: store completion status at show/season/episode level
# DONE 0.7.0: store status information in sqlite tables
# DONE 0.7.1: superchatty logging for underskore
# NEW  0.7.1: Threading can be toggled
# FIX? 0.7.1: POSSIBLE FIX for Underskore's thing
#             https://discord.com/channels/822460010649878528/822460010649878531/1104506813111603322
#             current_posters/TV Show(s)/Adam Savage's Tested-None/Doctor Who (2005) -001-current-local.jpg
#      0.7.1 removed some code that would have attempted multiple downloads for seasons and episodes
#      0.7.1 EXIF source comment disabled
#      0.7.1 Check URL before queueing the potential download
#      0.7.1 Delete leftover completion and URL files
#      0.7.1 Move "IF TRACK COMPLETION" into get/set methods
#      0.7.1 Only report queue size if there is a queue
# FIX  0.7.2 If fallback date is < 1/1/1970 and we're on Windows, set it to None
#            Patch for windows crash on old dates
# NEW  0.7.3 EVEN MORE SUPERCHAT to track down a Windows issue
# FIX  0.7.4 Orderly failure if a Plex item has no "locations"
#            observed by wogsurfer 🇲🇹 on Kometa Discord [running Windows, movies library doesn't show the problem]
#      0.7.5 report libraries found on the server on connect and in "can't find the library" message
#      0.7.6 DEFAULT_YEARS_BACK=0 means "no fallback date, grab everything"
#      0.7.6 support RESET_LIBRARIES=ALL_LIBRARIES
# FIX  0.7.7 allow empty or missing  RESET_LIBRARIES setting
# FIX  0.7.8 missed a couple logging.info calls
#      0.7.9 Check for and optionally delete Kometa-overlaid images
#      0.8.0 Use asset naming if only current OR depth = 1
#      0.8.1 or not OR
#      0.8.2 look for and handle TCM-overlaid images
#      0.8.2a add a 'global SCRIPT_STRING' to try to get rid of a "local variable 'SCRIPT_STRING' referenced before assignment A Knife and No Coin"
#      0.8.3 refactor and remove totalViewSize()
#      0.8.4 simplify logic around fallback_date
#      0.8.5 fix None fallback_date on Windows
#      0.8.6 strip trailing slash on Plex URL
#      0.8.7 suboptimal solution to names containing slashes
#      0.8.8 more logging about why we're skipping collections
#      0.8.9 fix logic error on string replace
#      0.8.9a don't report a spurious error due to missing collection
#      0.8.9b change one blogger to plogger since there's no bar in that context
#      0.8.9c use sanitize_filename on illegal names and actually use that name

SCRIPT_NAME = Path(__file__).stem

VERSION = "0.8.9c"

env_file_path = Path(".env")

# print(f"{env_file_path.read_text()}")
# current dateTime
now = datetime.now()

IS_WINDOWS = platform.system() == "Windows"

# convert to string
RUNTIME_STR = now.strftime("%Y-%m-%d %H:%M:%S")

ACTIVITY_LOG = f"{SCRIPT_NAME}.log"
DOWNLOAD_LOG = f"{SCRIPT_NAME}-dl.log"
SUPERCHAT = False

def superchat(the_msg, level, logfile):
    """ Superchat """
    if SUPERCHAT:
        logger(the_msg, level, logfile)

setup_logger('activity_log', ACTIVITY_LOG)
setup_logger('download_log', DOWNLOAD_LOG)

plogger(f"Starting {SCRIPT_NAME} {VERSION} at {RUNTIME_STR}", 'info', 'a')

if load_and_upgrade_env(env_file_path) < 0:
    sys.exit()

ID_FILES = True

URL_ARRAY = []
# no one using this yet
# QUEUED_DOWNLOADS = {}

STOP_FILE_NAME = "stop.dat"
SKIP_FILE_NAME = "skip.dat"

try:
    DEFAULT_YEARS_BACK = abs(int(os.getenv("DEFAULT_YEARS_BACK")))
except: # pylint: disable=bare-except
    plogger(f"DEFAULT_YEARS_BACK: {os.getenv('DEFAULT_YEARS_BACK')} not an integer. Defaulting to 1", 'info', 'a')
    DEFAULT_YEARS_BACK = 1

WEEKS_BACK = 52 * DEFAULT_YEARS_BACK

FALLBACK_DATE = None

if DEFAULT_YEARS_BACK > 0:
    FALLBACK_DATE = now - timedelta(weeks = WEEKS_BACK)

epoch = datetime(1970,1,1)
if IS_WINDOWS and FALLBACK_DATE is not None and FALLBACK_DATE < epoch:
    FALLBACK_DATE = None

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
POSTER_DIR = os.getenv("POSTER_DIR")

SUPERCHAT = os.getenv("SUPERCHAT")

if POSTER_DIR is None:
    POSTER_DIR = 'extracted_posters'

try:
    POSTER_DEPTH = int(os.getenv("POSTER_DEPTH"))
except: # pylint: disable=bare-except
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
RETAIN_OVERLAID_IMAGES = booler(os.getenv("RETAIN_OVERLAID_IMAGES"))
FIND_OVERLAID_IMAGES = booler(os.getenv("FIND_OVERLAID_IMAGES"))
RETAIN_KOMETA_OVERLAID_IMAGES = booler(os.getenv("RETAIN_TCM_IMAGES"))
RETAIN_TCM_OVERLAID_IMAGES = booler(os.getenv("RETAIN_TCM_IMAGES"))

if RETAIN_OVERLAID_IMAGES:
    RETAIN_KOMETA_OVERLAID_IMAGES = RETAIN_OVERLAID_IMAGES
    RETAIN_TCM_OVERLAID_IMAGES = RETAIN_OVERLAID_IMAGES


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
    RESET_ARRAY = ['PLACEHOLDER_VALUE_XYZZY']

RESET_COLLECTIONS = os.getenv("RESET_COLLECTIONS")

if RESET_COLLECTIONS:
    RESET_COLL_ARRAY = [s.strip() for s in RESET_COLLECTIONS.split(",")]
else:
    RESET_COLL_ARRAY = ['PLACEHOLDER_VALUE_XYZZY']


if LIBRARY_NAMES:
    LIB_ARRAY = [s.strip() for s in LIBRARY_NAMES.split(",")]
else:
    LIB_ARRAY = [LIBRARY_NAME]

ONLY_THESE_COLLECTIONS = os.getenv("ONLY_THESE_COLLECTIONS")

if ONLY_THESE_COLLECTIONS:
    COLLECTION_ARRAY = [s.strip() for s in ONLY_THESE_COLLECTIONS.split("|")]
else:
    COLLECTION_ARRAY = []

THREADED_DOWNLOADS = booler(os.getenv("THREADED_DOWNLOADS"))
plogger(f"Threaded downloads: {THREADED_DOWNLOADS}", 'info', 'a')

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

def get_asset_names(tgt_item):
    """ Get the asset names """
    ret_val = {}
    item_file = None

    superchat(f"entering get_asset_names {tgt_item}", 'info', 'a')

    ret_val['poster'] = "poster"
    ret_val['background'] = "background"
    ret_val['asset'] = None

    if tgt_item.TYPE == "collection":
        superchat("It's a collection", 'info', 'a')

        asset_name = tgt_item.title

        ret_val['asset'] = f"{asset_name}"
    elif tgt_item.TYPE == "movie":
        superchat("It's a movie", 'info', 'a')
        try:
            item_file = Path(tgt_item.media[0].parts[0].file)
            superchat(f"item_file {item_file}", 'info', 'a')
            asset_name = item_file.parts[len(item_file.parts)-2]
            superchat(f"ASSET_NAME {asset_name}", 'info', 'a')

            ret_val['asset'] = f"{asset_name}"
        except Exception as ex: # pylint: disable=broad-exception-caught
            plogger("unable to retrieve movie file", 'info', 'a')
            superchat(f"{ex}", 'info', 'a')
    elif tgt_item.TYPE == "show":
        superchat("It's a show", 'info', 'a')
        try:
            item_file = Path(tgt_item.locations[0])
            superchat(f"item_file {item_file}", 'info', 'a')
            superchat(f"item_file.parts {item_file.parts}", 'info', 'a')
            superchat(f"Trying to grab item_file.parts[{len(item_file.parts)-1}]", 'info', 'a')

            asset_name = item_file.parts[len(item_file.parts)-1]
            superchat(f"ASSET_NAME {asset_name}", 'info', 'a')

            ret_val['asset'] = f"{asset_name}"
        except Exception as ex: # pylint: disable=broad-exception-caught
            plogger("unable to retrieve show locations", 'info', 'a')
            superchat(f"{ex}", 'info', 'a')
    elif tgt_item.TYPE == "season":
        superchat("It's a season", 'info', 'a')
        try:
            item_file = Path(tgt_item.show().locations[0])
            superchat(f"item_file {item_file}", 'info', 'a')
            superchat(f"item_file.parts {item_file.parts}", 'info', 'a')
            superchat(f"Trying to grab item_file.parts[{len(item_file.parts)-1}]", 'info', 'a')

            asset_name = item_file.parts[len(item_file.parts)-1]
            superchat(f"ASSET_NAME {asset_name}", 'info', 'a')

            ret_val['poster'] = f"Season{str(tgt_item.seasonNumber).zfill(2)}"
            ret_val['background'] = f"{ret_val['poster']}_background"
            ret_val['asset'] = f"{asset_name}"
        except Exception as ex: # pylint: disable=broad-exception-caught
            plogger("unable to retrieve show locations", 'info', 'a')
            superchat(f"{ex}", 'info', 'a')
    elif tgt_item.TYPE == "episode":
        superchat("It's an episode", 'info', 'a')
        try:
            item_file = Path(tgt_item.media[0].parts[0].file)
            superchat(f"item_file {item_file}", 'info', 'a')
            superchat(f"item_file.parts {item_file.parts}", 'info', 'a')
            superchat(f"Trying to grab item_file.parts[{len(item_file.parts)-3}]", 'info', 'a')

            asset_name = item_file.parts[len(item_file.parts)-3]
            superchat(f"ASSET_NAME {asset_name}", 'info', 'a')

            ret_val['poster'] = f"{get_se_str(tgt_item)}"
            ret_val['background'] = f"{ret_val['poster']}_background"
            ret_val['asset'] = f"{asset_name}"
        except Exception as ex: # pylint: disable=broad-exception-caught
            plogger("unable to retrieve episode file", 'info', 'a')
            superchat(f"{ex}", 'info', 'a')
    else:
        # Don't support it
        superchat(f"This script doesn't support {tgt_item.TYPE}", 'info', 'a')
        ret_val['poster'] = None
        ret_val['background'] = None
        ret_val['asset'] = None

    return ret_val

TOPLEVEL_TMID = ""
TOPLEVEL_TVID = ""

def get_lib_setting(tgt_lib, the_setting): # pylint: disable=inconsistent-return-statements
    """ Get the library setting """
    settings = tgt_lib.settings()
    for setting in settings:
        if setting.id == the_setting:
            return setting.value

def get_subdir(tgt_item):
    """ Get the subdirectory """
    global TOPLEVEL_TMID, TOPLEVEL_TVID
    superchat(f"entering get_subdir {tgt_item}", 'info', 'a')
    ret_val = ""
    se_str = get_se_str(tgt_item)
    superchat(f"se_str {se_str}", 'info', 'a')
    s_bit = se_str[:3]
    superchat(f"s_bit {s_bit}", 'info', 'a')

    # collection-Adam-12 Collection
    # for assets we would want:
    # Adam-12 Collection
    # but don't forget to deal with Alien / Predator

    if USE_ASSET_NAMING:
        superchat(f"about to get asset names {tgt_item}", 'info', 'a')
        asset_details = get_asset_names(tgt_item)
        superchat(f"asset_details {asset_details}", 'info', 'a')
        return asset_details['asset']

    level_01 = None # 9-1-1 Lone Star-89393
    level_02 = None # S01-Season 1
    level_03 = None # S01E01-Pilot

    if tgt_item.type == 'collection':
        level_01, l_msg = validate_filename(f"collection-{tgt_item.title}") # pylint: disable=unused-variable
    else:
        imdbid, tmid, tvid = get_ids(tgt_item.guids) # pylint: disable=unused-variable
        if tgt_item.type == 'season':
            level_01, l_msg = validate_filename(f"{tgt_item.parentTitle}-{TOPLEVEL_TMID}") # show level
            safe_season_title, l_msg = validate_filename(tgt_item.title)
            level_02 = f"{s_bit}-{safe_season_title}"
        elif tgt_item.type == 'episode':
            level_01, l_msg = validate_filename(f"{tgt_item.grandparentTitle}-{TOPLEVEL_TMID}") # show level
            safe_season_title, l_msg = validate_filename(tgt_item.parentTitle)
            level_02 = f"{s_bit}-{safe_season_title}"
            safe_episode_title, l_msg = validate_filename(tgt_item.title)
            level_03 = f"{se_str}-{safe_episode_title}" # episode level
        else:
            TOPLEVEL_TMID = tmid
            TOPLEVEL_TVID = tvid
            level_01, l_msg = validate_filename(f"{tgt_item.title}-{TOPLEVEL_TMID}") # show level

    superchat(f"level_01 {level_01}", 'info', 'a')
    superchat(f"level_02 {level_02}", 'info', 'a')
    superchat(f"level_03 {level_03}", 'info', 'a')

    ret_val = Path(level_01)
    if level_02:
        ret_val = Path(ret_val, level_02)
    if level_03:
        ret_val = Path(ret_val, level_03)

    return str(ret_val)

def get_progress_string(tgt_item):
    """ Get the progress string """
    if tgt_item.TYPE == "season":
        ret_val = f"{tgt_item.parentTitle} - {get_se_str(tgt_item)} - {tgt_item.title}"
    elif tgt_item.TYPE == "episode":
        ret_val = f"{tgt_item.grandparentTitle} - {tgt_item.parentTitle} - {get_se_str(tgt_item)} - {tgt_item.title}"
    else:
        ret_val = f"{tgt_item.title}"

    return ret_val

def get_image_name(params, tgt_ext, background=False):
    """ Get the image name """
    ret_val = ""

    item_type = params['type']
    item_title = params['title']
    item_season = params['seasonNumber']
    item_se_str = params['se_str']

    idx = params['idx']
    provider = params['provider']
    source = params['source']
    safe_name, the_msg = validate_filename(item_title) # pylint: disable=unused-variable

    if USE_ASSET_NAMING:
        if ONLY_CURRENT or (POSTER_DEPTH == 1):
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
            if item_type in ('season', 'episode'):
                ret_val = f"{item_se_str}-{safe_name}-{base_name}"
            else:
                ret_val = f"{safe_name}-{base_name}"

    ret_val = ret_val.replace("--", "-")
    return ret_val

executor = ThreadPoolExecutor()
my_futures = []

def process_the_thing(params):
    """ Process the thing """
    global SCRIPT_STRING

    # tmid = params['tmid']
    # tvid = params['tvid']
    # item_type = params['type']
    # item_season = params['seasonNumber']
    # item_episode = params['episodeNumber']
    # item_se_str = params['se_str']

    idx = params['idx']
    folder_path = params['path']
    # current_posters/all_libraries/collection-Adam-12 Collection'
    # for assets this should be:
    # assets/One Show/Adam-12 Collection

    background = params['background']
    src_url = params['src_url']
    provider = params['provider']
    source = params['source']

    uuid = params['uuid']
    lib_title = params['lib_title']

    rv_result = {}
    rv_result['success'] = False
    rv_result['status'] = 'Nothing happened'

    tgt_ext = ".dat" if ID_FILES else ".jpg"
    tgt_filename = get_image_name(params, tgt_ext, background)
    # in asset case, I have '_poster.ext'
    superchat(f"target filename {tgt_filename}", 'info', 'a')

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
    superchat(f"final file path {final_file_path}", 'info', 'a')

    if not check_for_images(final_file_path):
        logger(f"{final_file_path} does not yet exist", 'info', 'd')
        if POSTER_DOWNLOAD:
            p = Path(folder_path)
            p.mkdir(parents=True, exist_ok=True)


            if not FOLDERS_ONLY:
                logger(f"provider: {provider} - source: {source} - downloading {redact(src_url, redaction_list)} to {tgt_filename}", 'info', 'd')
                try:
                    thumbpath = download(
                        f"{src_url}",
                        plex_token,
                        filename=tgt_filename,
                        savepath=folder_path,
                    )
                    logger(f"Downloaded {thumbpath}", 'info', 'd')

                    # Wait between items in case hammering the Plex server turns out badly.
                    time.sleep(DELAY)

                    local_file = str(rename_by_type(final_file_path))

                    if not KEEP_JUNK:
                        if local_file.find('.del') > 0:
                            superchat(f"deleting {local_file}", 'info', 'a')
                            os.remove(local_file)

                    if ADD_SOURCE_EXIF_COMMENT:
                        superchat("EXIF OPERATIONS DISABLED", 'info', 'a')
                        # exif_tag = 'plex internal'

                        # if source == 'remote':
                        #     exif_tag = src_url

                        # superchat(f"Adding user comment EXIF containing {exif_tag}", 'info', 'a')
                        # # Write out exif data
                        # # load existing exif data from image
                        # exif_dict = piexif.load(local_file)
                        # print(exif_dict)
                        # # insert custom data in usercomment field
                        # exif_dict["Exif"][piexif.ExifIFD.UserComment] = piexif.helper.UserComment.dump(
                        #     exif_tag,
                        #     encoding="unicode"
                        # )
                        # # insert mutated data (serialised into JSON) into image
                        # piexif.insert(
                        #     piexif.dump(exif_dict),
                        #     local_file
                        # )

                    add_url(src_url, uuid, lib_title)

                    # with open(URL_FILE_NAME, "a", encoding="utf-8") as sf:
                    #     sf.write(f"{src_url}{os.linesep}")

                    if TRACK_IMAGE_SOURCES:
                        with open(SOURCE_FILE_NAME, "a", encoding="utf-8") as sf:
                            sf.write(f"{local_file} - {redact(src_url, redaction_list)}{os.linesep}")

                except Exception as ex: # pylint: disable=broad-exception-caught
                    rv_result['success'] = False
                    rv_result['status'] = f"{ex}"
                    logger(f"error on {src_url} - {ex}", 'info', 'd')
        else:
            mkdir_flag = "" if IS_WINDOWS else "-p "
            script_line_start = ""
            if idx == 1:
                script_line_start = f'mkdir {mkdir_flag}"{folder_path}"{os.linesep}'

            script_line = f'{script_line_start}curl -C - -fLo "{os.path.join(folder_path, tgt_filename)}" "{src_url}"'

            SCRIPT_STRING = (
                SCRIPT_STRING + f"{script_line}{os.linesep}"
            )
    else:
        plogger(f"SKIP EXISTING {final_file_path}", 'info', 'a')

    return rv_result

class PosterPlaceholder: # pylint: disable=too-few-public-methods
    """ Placeholder for a poster object """
    def __init__(self, provider, key):
        """ Initialize the object """
        self.provider = provider
        self.key = key

def get_art(tgt_item, artwork_path, tmid, tvid, uuid, lib_title): # pylint: disable=too-many-branches, too-many-statements, too-many-locals, too-many-arguments, too-many-positional-arguments
    """ Get the artwork for the item """
    superchat(f"entering get_art {tgt_item.title}, {artwork_path}, {tmid}, {tvid}, {uuid}, {lib_title}", 'info', 'a')

    attempts = 0
    if ONLY_CURRENT:
        all_art = []
        all_art.append(PosterPlaceholder('current', tgt_item.art))
    else:
        all_art = tgt_item.arts()

    if USE_ASSET_NAMING:
        bg_path = artwork_path
    else:
        bg_path = Path(artwork_path, "backgrounds")

    while attempts < 5: # pylint: disable=too-many-nested-blocks
        try:
            progress_str = f"{get_progress_string(tgt_item)} - {len(all_art)} backgrounds"

            blogger(progress_str, 'info', 'a', bar)

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
                full_for_now = count >= POSTER_DEPTH > 0
                no_point_in_looking = full_for_now or no_more_to_get
                if no_more_to_get:
                    logger(f"Grabbed all available posters: {no_more_to_get}", 'info', 'a')
                if full_for_now:
                    logger(f"full_for_now: {full_for_now} - {POSTER_DEPTH} image(s) retrieved already", 'info', 'a')

            if not no_point_in_looking:
                idx = 1
                for art in all_art:
                    if art.key is not None:
                        if idx > POSTER_DEPTH > 0:
                            logger(f"Reached max depth of {POSTER_DEPTH}; exiting loop", 'info', 'a')
                            break

                        art_params = {}
                        art_params['tmid'] = tmid
                        art_params['tvid'] = tvid
                        art_params['idx'] = idx
                        art_params['path'] = bg_path
                        art_params['provider'] = art.provider
                        art_params['source'] = 'remote'
                        art_params['uuid'] = uuid
                        art_params['lib_title'] = lib_title

                        art_params['type'] = tgt_item.TYPE
                        art_params['title'] = tgt_item.title

                        try:
                            art_params['seasonNumber'] = tgt_item.seasonNumber
                        except: # pylint: disable=bare-except
                            art_params['seasonNumber'] = None

                        try:
                            art_params['episodeNumber'] = tgt_item.episodeNumber
                        except: # pylint: disable=bare-except
                            art_params['episodeNumber'] = None

                        art_params['se_str'] = get_se_str(tgt_item)

                        art_params['background'] = True

                        src_url = art.key
                        if src_url[0] == "/":
                            src_url = f"{plex_url}{art.key}&X-Plex-Token={plex_token}"
                            art_params['source'] = 'local'

                        art_params['src_url'] = src_url

                        bar.text = f"{progress_str} - {idx}"
                        logger(f"processing {progress_str} - {idx}", 'info', 'a')

                        superchat(f"Built out params for {tgt_item.title}: {art_params}", 'info', 'a')
                        if not TRACK_URLS or (TRACK_URLS and not check_url(src_url, uuid)):
                            if THREADED_DOWNLOADS:
                                my_future = executor.submit(process_the_thing, art_params) # does not block
                                # append it to the queue
                                my_futures.append(my_future)
                                superchat(f"Added {tgt_item.title} to the download queue", 'info', 'a')
                            else:
                                superchat(f"Downloading {tgt_item.title} directly", 'info', 'a')
                                process_the_thing(art_params)
                        else:
                            logger(f"SKIPPING {tgt_item.title} as its URL was found in the URL tracking table: {src_url} ", 'info', 'a')

                    else:
                        logger("skipping empty internal art object", 'info', 'a')

                    idx += 1

            attempts = 6
        except Exception as ex: # pylint: disable=broad-exception-caught
            progress_str = f"EX: {ex} {tgt_item.title}"
            logger(progress_str, 'info', 'a')
            attempts  += 1

def get_posters(p_lib, p_item, p_uuid, p_title): # pylint: disable=too-many-branches, too-many-statements, too-many-locals
    """ Get the posters for the item """
    superchat(f"entering get_posters {p_lib}, {p_item}, {p_uuid}, {p_title}", 'info', 'a')

    imdbid = None
    tmid = None
    tvid = None
    # uuid = uuid
    lib_title = p_title

    collection_title = None
    movie_title = None
    show_title = None
    season_title = None
    episode_title = None

    if p_item.type != 'collection':
        imdbid, tmid, tvid = get_ids(p_item.guids)
        if p_item.type == "show":
            show_title = p_item.title
        if p_item.type == "movie":
            movie_title = p_item.title
        if p_item.type == "season":
            show_title = p_item.parentTitle
            season_title = p_item.title
        if p_item.type == "episode":
            show_title = p_item.grandparentTitle
            season_title = p_item.parentTitle
            episode_title = p_item.title
    else:
        collection_title = p_item.title

    superchat(f"This {p_item.type} is called {p_item.title}", 'info', 'a')
    superchat(f"IDs: {imdbid}, {tmid}, {tvid}", 'info', 'a')
    superchat(f"collection_title: {collection_title}", 'info', 'a')
    superchat(f"movie_title:      {movie_title}", 'info', 'a')
    superchat(f"show_title:       {show_title}", 'info', 'a')
    superchat(f"season_title:     {season_title}", 'info', 'a')
    superchat(f"episode_title:    {episode_title}", 'info', 'a')

    if USE_ASSET_NAMING:
        tgt_dir = ASSET_DIR
        if ASSETS_BY_LIBRARIES:
            tgt_dir = os.path.join(tgt_dir, p_lib)
    else:
        if POSTER_CONSOLIDATE:
            tgt_dir = os.path.join(POSTER_DIR, "all_libraries")
        else:
            tgt_dir = os.path.join(POSTER_DIR, p_lib)

    superchat(f"Target directory for {p_item.title} artwork: {tgt_dir}", 'info', 'a')
    # current_posters/all_libraries
    # for assets we want:
    # assets/One Show

    # add a letter level here.
    if USE_ASSET_SUBFOLDERS:
        if p_item.type == 'collection':
            tgt_dir = os.path.join(tgt_dir, "Collections")
        else:
            # TODO: This is broken as it doesn't account for The in season/episode cases
            asset_subdir_target = p_item.titleSort
            if p_item.type in ('season', 'episode'):
                asset_subdir_target = show_title
            tgt_dir = os.path.join(tgt_dir, get_letter_dir(asset_subdir_target))

    superchat(f"final top-level directory for {p_item.title} artwork: {tgt_dir}", 'info', 'a')

    if not os.path.exists(tgt_dir):
        superchat("makin' dirs", 'info', 'a')
        os.makedirs(tgt_dir)

    attempts = 0

    superchat(f"about to get the subdir for {p_item}", 'info', 'a')

    item_path= get_subdir(p_item)

    if item_path is not None: # pylint: disable=too-many-nested-blocks
        superchat(f"item target directory for {p_item.title} artwork: {item_path}", 'info', 'a')
        # collection-Adam-12 Collection
        # for assets we would want:
        # Adam-12 Collection

        new_path = sanitize_filename(item_path)

        if new_path != item_path and USE_ASSET_NAMING:
            plogger(f"modified '{item_path}' to '{new_path}'; this will need to be renamed for asset use", 'info', 'a')

        artwork_path = Path(tgt_dir, new_path)
        logger(f"final artwork_path: {artwork_path}", 'info', 'a')

        # current_posters/all_libraries/collection-Adam-12 Collection'
        # for assets this should be:
        # assets/One Show/Adam-12 Collection

        attempts = 0
        if ONLY_CURRENT:
            superchat(f"only grabbing current artwork for {p_item.title}", 'info', 'a')
            all_posters = []
            all_posters.append(PosterPlaceholder('current', p_item.thumb))
        else:
            superchat(f"grabbing ALL artwork for {p_item.title}", 'info', 'a')
            all_posters = p_item.posters()
            superchat(f"{len(all_posters)} poster[s] available for {p_item.title}", 'info', 'a')

        while attempts < 5:
            superchat(f"attempt {attempts+1} at grabbing artwork for {p_item.title}", 'info', 'a')
            try:
                progress_str = f"{get_progress_string(p_item)} - {len(all_posters)} posters"

                plogger(progress_str, 'info', 'a')

                if ONLY_CURRENT:
                    no_point_in_looking = False
                else:
                    count = 0
                    posters_to_go = 0

                    if USE_ASSET_NAMING:
                        search_filter = "poster*.*"
                    else:
                        search_filter = "*.*"

                    if p_item.type == "season":
                        search_filter = f"Season{str(p_item.seasonNumber).zfill(2)}*.*"
                    if p_item.type == "episode":
                        search_filter = f"{get_se_str(p_item)}*.*"

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
                    full_for_now = count >= POSTER_DEPTH > 0
                    no_point_in_looking = full_for_now or no_more_to_get
                    if no_more_to_get:
                        logger(f"Grabbed all available posters: {no_more_to_get}", 'info', 'a')
                    if full_for_now:
                        logger(f"full_for_now: {full_for_now} - {POSTER_DEPTH} image(s) retrieved already", 'info', 'a')

                if not no_point_in_looking:
                    idx = 1
                    for poster in all_posters:
                        if idx > POSTER_DEPTH > 0:
                            logger(f"Reached max depth of {POSTER_DEPTH}; exiting loop", 'info', 'a')
                            break

                        art_params = {}
                        art_params['rating_key'] = p_item.ratingKey
                        art_params['tmid'] = tmid
                        art_params['tvid'] = tvid
                        # art_params['item'] = item
                        art_params['idx'] = idx
                        art_params['path'] = artwork_path
                        art_params['provider'] = poster.provider
                        art_params['source'] = 'remote'

                        art_params['type'] = p_item.TYPE
                        art_params['title'] = p_item.title

                        art_params['uuid'] = p_uuid
                        art_params['lib_title'] = lib_title

                        try:
                            art_params['seasonNumber'] = p_item.seasonNumber
                        except: # pylint: disable=bare-except
                            art_params['seasonNumber'] = None

                        try:
                            art_params['episodeNumber'] = p_item.episodeNumber
                        except: # pylint: disable=bare-except
                            art_params['episodeNumber'] = None

                        art_params['se_str'] = get_se_str(p_item)

                        art_params['background'] = False

                        src_url = poster.key

                        if src_url[0] == "/":
                            src_url = f"{plex_url}{poster.key}&X-Plex-Token={plex_token}"
                            art_params['source'] = 'local'

                        art_params['src_url'] = src_url

                        bar.text = f"{progress_str} - {idx}"
                        logger(f"processing {progress_str} - {idx}", 'info', 'a')

                        superchat(f"Built out params for {p_item.title}: {art_params}", 'info', 'a')
                        if not TRACK_URLS or (TRACK_URLS and not check_url(src_url, p_uuid)):
                            if THREADED_DOWNLOADS:
                                l_future = executor.submit(process_the_thing, art_params) # does not block
                                # append it to the queue
                                my_futures.append(l_future)
                                superchat(f"Added {p_item.title} to the download queue", 'info', 'a')
                            else:
                                superchat(f"Downloading {p_item.title} directly", 'info', 'a')
                                process_the_thing(art_params)
                        else:
                            logger(f"SKIPPING {p_item.title} as its URL was found in the URL tracking table: {src_url} ", 'info', 'a')

                        idx += 1

                attempts = 6
            except Exception as ex: # pylint: disable=broad-exception-caught
                progress_str = f"EX: {ex} {p_item.title}"
                logger(progress_str, 'info', 'a')

                attempts  += 1

        if GRAB_BACKGROUNDS:
            get_art(p_item, artwork_path, tmid, tvid, p_uuid, lib_title)
    else:
        plogger('Skipping {item.title}, error determining target subdirectory', 'info', 'a')

def rename_by_type(target):
    """ Rename a file based on its type """

    p = Path(target)

    kind = filetype.guess(target)
    if kind is None:
        with open(target, 'r') as file: # pylint: disable=unspecified-encoding
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
        logger(f"changing image extension to {extension} on {target}", 'info', 'a')

    # check for overlay exif tag
    if FIND_OVERLAID_IMAGES:
        kometa_overlay, tcm_overlay = has_overlay(target)
        if kometa_overlay or tcm_overlay:
            logger(f"kometa_overlay: {kometa_overlay}, tcm_overlay: {tcm_overlay} on image: {target}", 'info', 'a')

        if not RETAIN_KOMETA_OVERLAID_IMAGES and kometa_overlay:
            logger(f"Marking as JUNK: Kometa-overlaid image: {target}", 'info', 'a')
            extension = ".del"
        if not RETAIN_TCM_OVERLAID_IMAGES and tcm_overlay:
            logger(f"Marking as JUNK: TCM-overlaid image: {target}", 'info', 'a')
            extension = ".del"

    new_name = p.with_suffix(extension)

    if "html" in extension:
        logger(f"deleting html file {p}", 'info', 'a')
        p.unlink()
    else:
        logger(f"changing filename to {new_name} on {p}", 'info', 'a')
        p.rename(new_name)

    return new_name

def add_script_line(artwork_path, poster_file_path, src_url_with_token):
    """ Add a line to the script string """
    if IS_WINDOWS:
        script_line = f'{os.linesep}mkdir "{artwork_path}"{os.linesep}curl -C - -fLo "{Path(artwork_path, poster_file_path)}" {src_url_with_token}'
    else:
        script_line = f'{os.linesep}mkdir -p "{artwork_path}" && curl -C - -fLo "{Path(artwork_path, poster_file_path)}" {src_url_with_token}'
    return f"{script_line}{os.linesep}"

for lib in LIB_ARRAY:
    if lib in ALL_LIB_NAMES:
        try:
            HIGHWATER = 0
            START_QUEUE_LENGTH = len(my_futures)

            if len(my_futures) > 0:
                plogger(f"queue length: {len(my_futures)}", 'info', 'a')

            plogger(f"Loading {lib} ...", 'info', 'a')
            the_lib = plex.library.section(lib)
            the_uuid = the_lib.uuid
            superchat(f"{the_lib} uuid {the_uuid}", 'info', 'a')

            if (the_lib.title in RESET_ARRAY or RESET_ARRAY[0] == 'ALL_LIBRARIES'):
                plogger(f"Resetting rundate for {the_lib.title} to {FALLBACK_DATE}...", 'info', 'a')
                last_run_lib = FALLBACK_DATE
            else:
                last_run_lib = get_last_run(the_uuid, the_lib.TYPE)

                if last_run_lib is None:
                    plogger(f"no last run date for {the_lib}, using {FALLBACK_DATE}", 'info', 'a')
                    last_run_lib = FALLBACK_DATE

            superchat(f"{the_lib} last run date: {last_run_lib}", 'info', 'a')

            ID_ARRAY = []
            the_title = the_lib.title
            superchat(f"This library is called {the_title}", 'info', 'a')
            title, msg = validate_filename(the_title)
            STATUS_FILE_NAME = f"ratingkeys-{title}-{the_uuid}-{POSTER_DEPTH}.txt"
            status_file = Path(STATUS_FILE_NAME)

            if TRACK_COMPLETION:
                if status_file.is_file():
                    superchat("There's an old-style completion file here", 'info', 'a')
                    with open(status_file) as fp: # pylint: disable=unspecified-encoding
                        IDX = 0
                        for line in fp:
                            add_key(line.strip(), the_uuid, TRACK_COMPLETION)
                            IDX += 1
                        logger(f"{IDX} URls loaded and stored in the DB", 'info', 'a')

                    superchat(f"DELETING {status_file}", 'info', 'a')
                    status_file.unlink()

            URL_FILE_NAME = f"urls-{title}-{the_uuid}.txt"
            url_file = Path(URL_FILE_NAME)

            if url_file.is_file():
                logger(f"Reading URLs from {url_file.resolve()}", 'info', 'a')
                with open(url_file) as fp: # pylint: disable=unspecified-encoding
                    IDX = 0
                    for line in fp:
                        add_url(line.strip(), the_uuid, title)
                        IDX += 1
                    logger(f"{IDX} URls loaded and stored in the DB", 'info', 'a')
                superchat(f"DELETING {url_file}", 'info', 'a')
                url_file.unlink()


            SOURCE_FILE_NAME = f"sources-{title}-{the_uuid}.txt"

            if INCLUDE_COLLECTION_ARTWORK:
                plogger(f"getting collections from [{lib}]...", 'info', 'a')

                items = the_lib.collections()
                item_total = len(items)
                plogger(f"{item_total} collection(s) retrieved...", 'info', 'a')

                TGT_EXT = ".dat"

                if item_total > 0:
                    with alive_bar(
                        item_total, dual_line=True, title="Grab Collection Posters"
                    ) as bar:
                        for item in items:
                            superchat(f"This collection is called {item.title}", 'info', 'a')

                            # guid: 'collection://175b6fe6-fe95-480c-8bb2-2c5052b03b7e'
                            if len(COLLECTION_ARRAY) == 0 or item.title in COLLECTION_ARRAY:

                                if not check_key(item.ratingKey, the_uuid, TRACK_COMPLETION):
                                    logger(f"Starting {item.title}", 'info', 'a')

                                    get_posters(lib, item, the_uuid, the_title)

                                    bar() # pylint: disable=not-callable

                                    add_key(item.ratingKey, the_uuid, TRACK_COMPLETION)

                                else:
                                    blogger(f"SKIPPING {item.title}; status complete", 'info', 'a', bar)
                            else:
                                blogger(f"SKIPPING {item.title}; not in a targeted collection", 'info', 'a', bar)
                                blogger(f"either len(COLLECTION_ARRAY) == 0: {len(COLLECTION_ARRAY)} or {item.title} is not in {COLLECTION_ARRAY}", 'info', 'a', bar)

            else:
                plogger("Skipping collection artwork ...", 'info', 'a')

            if not ONLY_COLLECTION_ARTWORK:

                if len(COLLECTION_ARRAY) == 0:
                    COLLECTION_ARRAY = ['placeholder_collection_name']

                for coll in COLLECTION_ARRAY:
                    LIB_KEY = f"{the_uuid}-{coll}"

                    items = []

                    if coll == 'placeholder_collection_name':
                        if last_run_lib is None:
                            plogger(f"Loading {the_lib.TYPE}s  ...", 'info', 'a')
                            ITEM_COUNT, items = get_all_from_library(the_lib, None, None)
                        else:
                            plogger(f"Loading {the_lib.TYPE}s new since {last_run_lib} ...", 'info', 'a')
                            ITEM_COUNT, items = get_all_from_library(the_lib, None, {"addedAt>>": last_run_lib})
                            last_run_lib = datetime.now()
                        plogger(f"Completed loading {len(items)} of {ITEM_COUNT} {the_lib.TYPE}(s) from {the_lib.title}", 'info', 'a')

                        if the_lib.TYPE == "show" and GRAB_SEASONS:
                            if the_lib.title in RESET_ARRAY:
                                plogger(f"Resetting SEASON rundate for {the_lib.title} to {FALLBACK_DATE}...", 'info', 'a')
                                last_run_season = FALLBACK_DATE
                            else:
                                last_run_season = get_last_run(the_uuid, 'season')

                            if last_run_season is None and FALLBACK_DATE is not None:
                                last_run_season = FALLBACK_DATE

                            if last_run_season is None:
                                plogger("Loading seasons ...", 'info', 'a')
                                season_count, seasons = get_all_from_library(the_lib, 'season', None)
                            else:
                                plogger(f"Loading seasons new since {last_run_season} ...", 'info', 'a')
                                season_count, seasons = get_all_from_library(the_lib, 'season', {"addedAt>>": last_run_season})
                                last_run_season = datetime.now()
                            plogger(f"Completed loading {len(seasons)} of {season_count} season(s) from {the_lib.title}", 'info', 'a')
                            items.extend(seasons)
                            superchat(f"{len(items)} items to examine", 'info', 'a')


                        if the_lib.TYPE == "show" and GRAB_EPISODES:
                            if the_lib.title in RESET_ARRAY:
                                plogger(f"Resetting EPISODE rundate for {the_lib.title} to {FALLBACK_DATE}...", 'info', 'a')
                                last_run_episode = FALLBACK_DATE
                            else:
                                last_run_episode = get_last_run(the_uuid, 'episode')

                            if last_run_episode is None and FALLBACK_DATE is not None:
                                last_run_episode = FALLBACK_DATE

                            if last_run_episode is None:
                                plogger("Loading episodes ...", 'info', 'a')
                                episode_count, episodes = get_all_from_library(the_lib, 'episode', None)
                            else:
                                plogger(f"Loading episodes new since {last_run_episode} ...", 'info', 'a')
                                episode_count, episodes = get_all_from_library(the_lib, 'episode', {"addedAt>>": last_run_episode})
                                last_run_episode = datetime.now()
                            plogger(f"Completed loading {len(episodes)} of {episode_count} episode(s) from {the_lib.title}", 'info', 'a')
                            items.extend(episodes)
                            superchat(f"{len(items)} items to examine", 'info', 'a')

                    else:
                        plogger(f"Loading everything in collection {coll} ...", 'info', 'a')
                        ITEM_COUNT, items = get_all_from_library(the_lib, None, {'collection': coll})
                        plogger(f"Completed loading {len(items)} from collection {coll}", 'info', 'a')

                    item_total = len(items)
                    if item_total > 0:
                        logger(f"looping over {item_total} items...", 'info', 'a')
                        ITEM_COUNT = 0

                        plex_links = []
                        external_links = []

                        with alive_bar(item_total, dual_line=True, title=f"Grab all posters {the_lib.title}") as bar:
                            for item in items:
                                try:
                                    if not check_key(item.ratingKey, the_uuid, TRACK_COMPLETION):
                                        blogger(f"Starting {item.TYPE}: {item.title}", 'info', 'a', bar)

                                        get_posters(lib, item, the_uuid, the_title)

                                        add_key(item.ratingKey, the_uuid, TRACK_COMPLETION)
                                    else:
                                        blogger(f"SKIPPING {item.title}; status complete", 'info', 'a', bar)

                                    ITEM_COUNT += 1
                                except Exception as ex: # pylint: disable=broad-exception-caught
                                    plogger(f"Problem processing {item.title}; {ex}", 'info', 'a')

                                bar() # pylint: disable=not-callable

                                stop_file = Path(STOP_FILE_NAME)
                                skip_file = Path(SKIP_FILE_NAME)

                                if stop_file.is_file() or skip_file.is_file():
                                    raise StopIteration

                        plogger(f"Processed {ITEM_COUNT} of {item_total}", 'info', 'a')

            PROGRESS_STR = "COMPLETE"
            logger(PROGRESS_STR, 'info', 'a')

            if last_run_lib is not None:
                add_last_run(the_uuid, the_lib.title, the_lib.TYPE, last_run_lib)
            if the_lib.TYPE == "show":
                try:
                    if GRAB_SEASONS and last_run_season is not None:
                        add_last_run(the_uuid, the_lib.title, 'season', last_run_season)
                    if GRAB_EPISODES and last_run_episode is not None:
                        add_last_run(the_uuid, the_lib.title, 'episode', last_run_episode)
                except NameError:
                    logger('no last run date to record', 'info', 'a')

            if not POSTER_DOWNLOAD:
                if len(SCRIPT_STRING) > 0:
                    with open(SCRIPT_FILE, "w", encoding="utf-8") as myfile:
                        myfile.write(f"{SCRIPT_STRING}{os.linesep}")

        except StopIteration:
            if stop_file.is_file():
                PROGRESS_STR = "stop file found, leaving loop"
            if skip_file.is_file():
                PROGRESS_STR = "skip file found, skipping library"

            plogger(PROGRESS_STR, 'info', 'a')

            if stop_file.is_file():
                stop_file.unlink()
                break
            if skip_file.is_file():
                skip_file.unlink()

        except Exception as ex: # pylint: disable=broad-exception-caught
            plogger(f"Problem processing {lib}; {ex}", 'info', 'a')
    else:
        logger(f"Library {lib} not found: available libraries on this server are: {ALL_LIB_NAMES}", 'info', 'a')

IDX = 1
MAX = len(my_futures)
if MAX > 0:
    plogger(f"waiting on {MAX} downloads", 'info', 'a')
# iterate over all submitted tasks and get results as they are available

for future in as_completed(my_futures):
    result = future.result() # blocks
    sys.stdout.write(f"\r{IDX}/{MAX}       ")
    sys.stdout.flush()
    # TODO: write status file down here
    IDX += 1

plogger("Complete!", 'info', 'a')
# shutdown the thread pool
executor.shutdown() # blocks
