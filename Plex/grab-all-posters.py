import json
import logging
import os
import platform
import re
import sys
import time
from multiprocessing import cpu_count
from multiprocessing.pool import ThreadPool
from pathlib import Path

import filetype
import piexif
import piexif.helper
import plexapi
import requests
from alive_progress import alive_bar
from dotenv import load_dotenv
from pathvalidate import ValidationError, validate_filename
from plexapi import utils
from plexapi.exceptions import Unauthorized
from plexapi.server import PlexServer
from plexapi.utils import download

from helpers import booler, get_all, get_ids, get_plex, redact, validate_filename

import logging
from pathlib import Path
SCRIPT_NAME = Path(__file__).stem

logging.basicConfig(
    filename=f"{SCRIPT_NAME}.log",
    filemode="w",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logging.info(f"Starting {SCRIPT_NAME}")
print(f"Starting {SCRIPT_NAME}")

if os.path.exists(".env"):
    load_dotenv()
else:
    logging.info(f"No environment [.env] file.  Exiting.")
    print(f"No environment [.env] file.  Exiting.")
    exit()

ID_FILES = True

URL_ARRAY = []
STATUS_FILE_NAME = "URLS.txt"

PLEX_URL = os.getenv("PLEX_URL")
PLEX_TOKEN = os.getenv("PLEX_TOKEN")

if PLEX_URL is None or PLEX_URL == 'https://plex.domain.tld':
    print("You must specify PLEX_URL in the .env file.")
    exit()

if PLEX_TOKEN is None or PLEX_TOKEN == 'PLEX-TOKEN':
    print("You must specify PLEX_TOKEN in the .env file.")
    exit()

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
GRAB_EPISODES = booler(os.getenv("GRAB_EPISODES"))
ONLY_CURRENT = booler(os.getenv("ONLY_CURRENT"))

if ONLY_CURRENT:
    POSTER_DIR = os.getenv("CURRENT_POSTER_DIR")

TRACK_URLS = booler(os.getenv("TRACK_URLS"))
ASSET_DIR = os.getenv("ASSET_DIR")

USE_ASSET_NAMING = booler(os.getenv("USE_ASSET_NAMING"))
USE_ASSET_FOLDERS = booler(os.getenv("USE_ASSET_FOLDERS"))
ASSETS_BY_LIBRARIES = booler(os.getenv("ASSETS_BY_LIBRARIES"))
NO_FS_WARNING = booler(os.getenv("NO_FS_WARNING"))

if not USE_ASSET_NAMING:
    USE_ASSET_FOLDERS = False
    ASSETS_BY_LIBRARIES = False
else:
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
        print("PMM asset aaming setup at this time.")
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

if LIBRARY_NAMES:
    LIB_ARRAY = [s.strip() for s in LIBRARY_NAMES.split(",")]
else:
    LIB_ARRAY = [LIBRARY_NAME]

imdb_str = "imdb://"
tmdb_str = "tmdb://"
tvdb_str = "tvdb://"

if USE_ASSET_NAMING:
    if not (USE_ASSET_NAMING and ONLY_CURRENT):
        str01 = f"USE_ASSET_NAMING: {USE_ASSET_NAMING} and ONLY_CURRENT: {ONLY_CURRENT}"
        str02 = f"Asset naming only works with only current artwork"

        logging.info(str01)
        print(str01)
        logging.info(str02)
        print(str02)

        exit()

redaction_list = []
redaction_list.append(PLEX_URL)
redaction_list.append(PLEX_TOKEN)

plex = get_plex(PLEX_URL, PLEX_TOKEN)

logging.info("connection success")

if LIBRARY_NAMES == 'ALL_LIBRARIES':
    LIB_ARRAY = []
    all_libs = plex.library.sections()
    for lib in all_libs:
        if lib.type == 'movie' or lib.type == 'show':
            LIB_ARRAY.append(lib.title.strip())

def download_url(args):
    t0 = time.time()
    url, fn = args[0], args[1]
    try:
        r = requests.get(url)
        with open(fn, 'wb') as f:
            f.write(r.content)
        return(url, time.time() - t0)
    except Exception as e:
        print('Exception in download_url():', e)

def download_parallel(args):
    cpus = cpu_count()
    results = ThreadPool(cpus - 1).imap_unordered(download_url, args)
    for result in results:
        print('url:', result[0], 'time (s):', result[1])

# urls = ['https://www.northwestknowledge.net/metdata/data/pr_1979.nc',
# 'https://www.northwestknowledge.net/metdata/data/pr_1980.nc',
# 'https://www.northwestknowledge.net/metdata/data/pr_1981.nc',
# 'https://www.northwestknowledge.net/metdata/data/pr_1982.nc']

# fns = [r'C:\Users\konrad\Downloads\pr_1979.nc',
# r'C:\Users\konrad\Downloads\pr_1980.nc',
# r'C:\Users\konrad\Downloads\pr_1981.nc',
# r'C:\Users\konrad\Downloads\pr_1982.nc']

# inputs = zip(urls, fns)

# download_parallel(inputs)

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

    if item_file is not None:
        logging.info(f"item_file: {item_file}")
        logging.info(f"ASSET_NAME: {ASSET_NAME}")

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
    item = params['item']
    idx = params['idx']
    provider = params['provider']
    source = params['source']
    safe_name, msg = validate_filename(item.title)

    if USE_ASSET_NAMING:
        base_name = f"{tgt_ext}"
        if background:
            ret_val = f"_background{base_name}"
        else:
            if item.TYPE == "season":
                # _Season##.ext
                # _Season##_background.ext
                ret_val = f"_Season{str(item.seasonNumber).zfill(2)}{base_name}"
            elif item.TYPE == "episode":
                # _S##E##.ext
                # _S##E##_background.ext
                ret_val = f"_{get_SE_str(item)}{base_name}"
            else:
                if USE_ASSET_FOLDERS:
                    ret_val = f"_poster{base_name}"
                else:
                    ret_val = f"{base_name}"

    else:
        base_name = f"{provider}-{source}-{str(idx).zfill(3)}{tgt_ext}"

        if background:
            ret_val = f"background-{base_name}"
        else:
            if item.TYPE == "season" or item.TYPE == "episode":
                ret_val = f"{get_SE_str(item)}-{safe_name}-{base_name}"
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
        os.remove(file_path)

    if jpg_here and png_here:
        os.remove(jpg_path)
        os.remove(png_path)

    if jpg_here or png_here:
        return True

    return False

def process_the_thing(params):

    tmid = params['tmid']
    tvid = params['tvid']
    item = params['item']
    idx = params['idx']
    folder_path = params['path']
    # current_posters/all_libraries/collection-Adam-12 Collection'
    # for assets this should be:
    # assets/One Show/Adam-12 Collection

    background = params['background']
    src_URL = params['src_URL']
    provider = params['provider']
    source = params['source']

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
            logging.info(
                f"{final_file_path} does not yet exist"
            )
            if POSTER_DOWNLOAD:
                p = Path(folder_path)
                p.mkdir(parents=True, exist_ok=True)


                logging.info(f"provider: {provider} - source: {source}")
                logging.info(f"downloading {redact(src_URL, redaction_list)}")
                logging.info(f"to {tgt_filename}")
                try:
                    thumbPath = download(
                        f"{src_URL}",
                        PLEX_TOKEN,
                        filename=tgt_filename,
                        savepath=folder_path,
                    )
                    logging.info(f"Downloaded {thumbPath}")

                    # Wait between items in case hammering the Plex server turns out badly.
                    time.sleep(DELAY)


                    local_file = str(rename_by_type(final_file_path))

                    if not KEEP_JUNK:
                        if local_file.find('.del') > 0:
                            os.remove(local_file)

                    # Write out exif data
                    # load existing exif data from image
                    # exif_dict = piexif.load(local_file)
                    # # insert custom data in usercomment field
                    # exif_dict["Exif"][piexif.ExifIFD.UserComment] = piexif.helper.UserComment.dump(
                    #     src_URL,
                    #     encoding="unicode"
                    # )
                    # # insert mutated data (serialised into JSON) into image
                    # piexif.insert(
                    #     piexif.dump(exif_dict),
                    #     local_file
                    # )

                    URL_ARRAY.append(src_URL)

                    with open(URL_FILE_NAME, "a", encoding="utf-8") as sf:
                        sf.write(f"{src_URL}{os.linesep}")

                except Exception as ex:
                    logging.info(f"error on {src_URL}")
                    logging.info(f"{ex}")
            else:
                mkdir_flag = "" if IS_WINDOWS else "-p "
                script_line_start = ""
                if idx == 1:
                    script_line_start = f'mkdir {mkdir_flag}"{folder_path}"{os.linesep}'

                script_line = f'{script_line_start}curl -C - -fLo "{os.path.join(folder_path, tgt_filename)}" "{src_URL}"'

                SCRIPT_STRING = (
                    SCRIPT_STRING + f"{script_line}{os.linesep}"
                )

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

            logging.info(progress_str)
            bar.text = progress_str

            import fnmatch

            if ONLY_CURRENT:
                no_point_in_looking = False
            else:
                count = 0
                posters_to_go = 0

                if os.path.exists(bg_path):
                    count = len(fnmatch.filter(os.listdir(bg_path), "*.*"))
                    logging.info(f"{count} files in {bg_path}")

                posters_to_go = count - POSTER_DEPTH

                if posters_to_go < 0:
                    poster_to_go = abs(posters_to_go)
                else:
                    poster_to_go = 0

                logging.info(
                    f"{poster_to_go} needed to reach depth {POSTER_DEPTH}"
                )

                no_more_to_get = count >= len(all_art)
                full_for_now = count >= POSTER_DEPTH and POSTER_DEPTH > 0
                no_point_in_looking = full_for_now or no_more_to_get
                if no_more_to_get:
                    logging.info(
                        f"Grabbed all available posters: {no_more_to_get}"
                    )
                if full_for_now:
                    logging.info(
                        f"full_for_now: {full_for_now} - {POSTER_DEPTH} image(s) retrieved already"
                    )

            if not no_point_in_looking:
                idx = 1
                for art in all_art:
                    if art.key is not None:
                        if POSTER_DEPTH > 0 and idx > POSTER_DEPTH:
                            logging.info(
                                f"Reached max depth of {POSTER_DEPTH}; exiting loop"
                            )
                            break

                        art_params = {}
                        art_params['tmid'] = tmid
                        art_params['tvid'] = tvid
                        art_params['item'] = item
                        art_params['idx'] = idx
                        art_params['path'] = bg_path
                        art_params['provider'] = art.provider
                        art_params['source'] = 'remote'

                        art_params['background'] = True

                        src_URL = art.key
                        if src_URL[0] == "/":
                            src_URL = f"{PLEX_URL}{art.key}&X-Plex-Token={PLEX_TOKEN}"
                            art_params['source'] = 'local'

                        art_params['src_URL'] = src_URL

                        bar.text = f"{progress_str} - {idx}"
                        logging.info("--------------------------------")
                        logging.info(f"processing {progress_str} - {idx}")

                        process_the_thing(art_params)
                    else: 
                        logging.info(f"skipping empty internal art object")

                    idx += 1

            attempts = 6
        except Exception as ex:
            progress_str = f"EX: {ex} {item.title}"
            logging.info(progress_str)

            attempts  += 1

def get_posters(lib, item):
    global SCRIPT_STRING

    imdbid = None
    tmid = None
    tvid = None

    if item.type != 'collection':
        imdbid, tmid, tvid = get_ids(item.guids, None)

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

    if not os.path.exists(tgt_dir):
        os.makedirs(tgt_dir)

    attempts = 0

    item_path= get_subdir(item)
    # collection-Adam-12 Collection
    # for assets we would want:
    # Adam-12 Collection
    artwork_path = Path(tgt_dir, item_path)
    logging.info(f"final artwork_path: {artwork_path}")
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

            logging.info(progress_str)
            bar.text = progress_str

            import fnmatch

            if ONLY_CURRENT:
                no_point_in_looking = False
            else:
                count = 0
                posters_to_go = 0

                if os.path.exists(artwork_path):
                    count = len(fnmatch.filter(os.listdir(artwork_path), "*.*"))
                    logging.info(f"{count} files in {artwork_path}")

                posters_to_go = count - POSTER_DEPTH

                if posters_to_go < 0:
                    poster_to_go = abs(posters_to_go)
                else:
                    poster_to_go = 0

                logging.info(
                    f"{poster_to_go} needed to reach depth {POSTER_DEPTH}"
                )

                no_more_to_get = count >= len(all_posters)
                full_for_now = count >= POSTER_DEPTH and POSTER_DEPTH > 0
                no_point_in_looking = full_for_now or no_more_to_get
                if no_more_to_get:
                    logging.info(
                        f"Grabbed all available posters: {no_more_to_get}"
                    )
                if full_for_now:
                    logging.info(
                        f"full_for_now: {full_for_now} - {POSTER_DEPTH} image(s) retrieved already"
                    )

            if not no_point_in_looking:
                idx = 1
                for poster in all_posters:
                    if POSTER_DEPTH > 0 and idx > POSTER_DEPTH:
                        logging.info(
                            f"Reached max depth of {POSTER_DEPTH}; exiting loop"
                        )
                        break

                    art_params = {}
                    art_params['tmid'] = tmid
                    art_params['tvid'] = tvid
                    art_params['item'] = item
                    art_params['idx'] = idx
                    art_params['path'] = artwork_path
                    art_params['provider'] = poster.provider
                    art_params['source'] = 'remote'

                    art_params['background'] = False

                    src_URL = poster.key

                    if src_URL[0] == "/":
                        src_URL = f"{PLEX_URL}{poster.key}&X-Plex-Token={PLEX_TOKEN}"
                        art_params['source'] = 'local'


                    art_params['src_URL'] = src_URL

                    bar.text = f"{progress_str} - {idx}"
                    logging.info("--------------------------------")
                    logging.info(f"processing {progress_str} - {idx}")

                    process_the_thing(art_params)

                    idx += 1

            attempts = 6
        except Exception as ex:
            progress_str = f"EX: {ex} {item.title}"
            logging.info(progress_str)

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
                logging.info('Contains 404, deleting')
                extension = ".del"
            else:
                logging.info('Cannot guess file type; using txt')
                extension = ".txt"
    else:
        extension = f".{kind.extension}"

    new_name = p.with_suffix(extension)

    if "html" in extension:
        logging.info(f"deleting html file {p}")
        p.unlink()
    else:
        logging.info(f"changing file extension to {extension}")
        p.rename(new_name)

    return new_name

def add_script_line(artwork_path, poster_file_path, src_URL_with_token):
    if IS_WINDOWS:
        script_line = f'{os.linesep}mkdir "{artwork_path}"{os.linesep}curl -C - -fLo "{Path(artwork_path, poster_file_path)}" {src_URL_with_token}'
    else:
        script_line = f'{os.linesep}mkdir -p "{artwork_path}" && curl -C - -fLo "{Path(artwork_path, poster_file_path)}" {src_URL_with_token}'
    return f"{script_line}{os.linesep}"

def bar_and_log(the_bar, msg):
    logging.info(msg)
    the_bar.text = msg

def download_file(src_URL, target_path, target_filename):
    p = Path(target_path)
    p.mkdir(parents=True, exist_ok=True)

    dlPath = download(
        f"{src_URL}", PLEX_TOKEN, filename=target_filename, savepath=target_path
    )
    rename_by_type(dlPath)

def get_file(src_URL, bar, item, target_path, target_file):
    if src_URL[0] == "/":
        src_URL_with_token = f"{PLEX_URL}{src_URL}?X-Plex-Token={PLEX_TOKEN}"
        src_URL = f"{PLEX_URL}{src_URL}"

    bar_and_log(bar, f"{item.title} - art: {src_URL}")

    if POSTER_DOWNLOAD:
        bar_and_log(bar, f"{item.title} - DOWNLOADING {target_file}")
        download_file(src_URL, target_path, target_file)
    else:
        bar_and_log(bar, f"{item.title} - building download command")
        SCRIPT_STRING += add_script_line(target_path, target_file, src_URL_with_token)

for lib in LIB_ARRAY:
    try:
        the_lib = plex.library.section(lib)

        id_array = []
        status_file_name = f"{the_lib.uuid}-{POSTER_DEPTH}.txt"
        status_file = Path(status_file_name)

        if status_file.is_file():
            with open(f"{status_file_name}") as fp:
                for line in fp:
                    id_array.append(line.strip())

        URL_ARRAY = []
        title, msg = validate_filename(f"{the_lib.title}")
        URL_FILE_NAME = f"{title}-{the_lib.uuid}.txt"
        url_file = Path(URL_FILE_NAME)

        if url_file.is_file():
            with open(f"{URL_FILE_NAME}") as fp:
                for line in fp:
                    URL_ARRAY.append(line.strip())

        if INCLUDE_COLLECTION_ARTWORK:
            print(f"getting collections from [{lib}]...")

            items = the_lib.collections()
            item_total = len(items)
            print(f"{item_total} collection(s) retrieved...")

            tgt_ext = ".dat"

            if item_total > 0:
                with alive_bar(
                    item_total, dual_line=True, title="Grab Collection Posters"
                ) as bar:
                    for item in items:

                        if id_array.count(f"{item.ratingKey}") == 0:
                            logging.info("================================")
                            logging.info(f"Starting {item.title}")

                            get_posters(lib, item)

                            bar()

                            id_array.append(item.ratingKey)

                            # write out item_array to file.
                            with open(status_file, "a", encoding="utf-8") as sf:
                                sf.write(f"{item.ratingKey}{os.linesep}")

                        else:
                            logging.info("================================")
                            logging.info(f"SKIPPING {item.title}; it's marked as complete")
                            bar.text = f"SKIPPING {item.title}; it's marked as complete"

        if not ONLY_COLLECTION_ARTWORK:
            items = get_all(plex, the_lib)
            item_total = len(items)
            logging.info(f"looping over {item_total} items...")
            item_count = 1

            plex_links = []
            external_links = []

            with alive_bar(item_total, dual_line=True, title=f"Grab all posters {the_lib.title}") as bar:
                for item in items:

                    if id_array.count(f"{item.ratingKey}") == 0:
                        logging.info("================================")
                        logging.info(f"Starting {item.title}")

                        get_posters(lib, item)

                        if item.TYPE == "show":
                            lib_ordering = get_lib_setting(the_lib, 'showOrdering')
                            show_ordering = item.showOrdering
                            if show_ordering is None:
                                show_ordering = lib_ordering

                            if GRAB_SEASONS:
                                # get seasons
                                seasons = item.seasons()

                                # loop over all:
                                for s in seasons:
                                    get_posters(lib, s)

                                    if GRAB_EPISODES:
                                        # get episodes
                                        episodes = s.episodes()

                                        # loop over all
                                        for e in episodes:
                                            get_posters(lib, e)

                        id_array.append(item.ratingKey)
                    else:
                        logging.info("================================")
                        logging.info(f"SKIPPING {item.title}; it's marked as complete")
                        bar.text = f"SKIPPING {item.title}; it's marked as complete"

                    # write out item_array to file.
                    with open(status_file, "a", encoding="utf-8") as sf:
                        sf.write(f"{item.ratingKey}{os.linesep}")

                    bar()

        progress_str = "COMPLETE"
        logging.info(progress_str)

        bar.text = progress_str

        print(os.linesep)
        if not POSTER_DOWNLOAD:
            scr_path = os.path.join(tgt_dir, SCRIPT_FILE)
            if len(SCRIPT_STRING) > 0:
                with open(scr_path, "w", encoding="utf-8") as myfile:
                    myfile.write(f"{SCRIPT_STRING}{os.linesep}")

    except Exception as ex:
        progress_str = f"Problem processing {lib}; {ex}"
        logging.info(progress_str)

        print(progress_str)
