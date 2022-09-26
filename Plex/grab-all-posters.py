import logging
import mimetypes
import os
import platform
import sys
import textwrap
from pathlib import Path, PurePath
from xmlrpc.client import Boolean
import time

USE_MAGIC = True
try:
    import magic
except:
    print("================== ATTENTION ==================")
    print("There was a problem importing the python-magic library")
    print("This typically means you haven't installed libmagic")
    print("Script will default to .jpg extension on all images")
    print("================== ATTENTION ==================")
    USE_MAGIC = False

import requests
from alive_progress import alive_bar
from dotenv import load_dotenv
from pathvalidate import is_valid_filename, sanitize_filename
from plexapi.exceptions import BadRequest, NotFound, Unauthorized
from plexapi.server import PlexServer
from plexapi.utils import download
from tmdbapis import TMDbAPIs
from helpers import booler, redact, getTID, validate_filename, getPath

load_dotenv()

logging.basicConfig(filename='grab-all-posters.log', filemode='w', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

logging.info('Starting grab-all-posters.py')

PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')
LIBRARY_NAME = os.getenv('LIBRARY_NAME')
LIBRARY_NAMES = os.getenv('LIBRARY_NAMES')
POSTER_DIR = os.getenv('POSTER_DIR')
POSTER_DEPTH = int(os.getenv('POSTER_DEPTH'))
POSTER_DOWNLOAD = booler(os.getenv('POSTER_DOWNLOAD'))
if not POSTER_DOWNLOAD:
    print("================== ATTENTION ==================")
    print("Downloading disabled; file identification not possible")
    print("Script will default to .jpg extension on all images")
    print("================== ATTENTION ==================")
    USE_MAGIC = False

POSTER_CONSOLIDATE = booler(os.getenv('POSTER_CONSOLIDATE'))
INCLUDE_COLLECTION_ARTWORK = booler(os.getenv('INCLUDE_COLLECTION_ARTWORK'))
ONLY_COLLECTION_ARTWORK = booler(os.getenv('ONLY_COLLECTION_ARTWORK'))
DELAY = int(os.getenv('DELAY'))

if not DELAY:
    DELAY = 0

if POSTER_DEPTH is None:
    POSTER_DEPTH = 0

SCRIPT_FILE = "get_images.sh"
SCRIPT_SEED = f"#!/bin/bash{os.linesep}{os.linesep}# SCRIPT TO GRAB IMAGES{os.linesep}{os.linesep}"
IS_WINDOWS = platform.system() == 'Windows'

if IS_WINDOWS:
    SCRIPT_FILE = "get_images.bat"
    SCRIPT_SEED = f"@echo off{os.linesep}{os.linesep}"

if POSTER_DOWNLOAD:
    script_string = SCRIPT_SEED
else:
    script_string = ""

if LIBRARY_NAMES:
    lib_array = LIBRARY_NAMES.split(",")
else:
    lib_array = [LIBRARY_NAME]

imdb_str = 'imdb://'
tmdb_str = 'tmdb://'
tvdb_str = 'tvdb://'

if USE_MAGIC:
    mime = magic.Magic(mime=True)

print(f"connecting to {PLEX_URL}...")
logging.info(f"connecting to {PLEX_URL}...")
try:
    plex = PlexServer(PLEX_URL, PLEX_TOKEN)
except Unauthorized:
    print("Plex Error: Plex token is invalid")
    exit()

logging.info(f"connection success")

def rename_by_type(target):
    p = Path(target)

    if USE_MAGIC:
        logging.info(f"determining file type of {target}")
        extension = mimetypes.guess_extension(mime.from_file(target), strict=False)
    else:
        logging.info(f"no libmagic; assuming {extension}")
        extension = ".jpg"

    if 'html' in extension:
        logging.info(f"deleting html file {p}")
        p.unlink()
    else:
        logging.info(f"changing file extension to {extension}")
        p.rename(p.with_suffix(extension))

def add_script_line(artwork_path, poster_file_path, src_URL_with_token):
    if IS_WINDOWS:
        script_line = f"{os.linesep}mkdir \"{artwork_path}\"{os.linesep}curl -C - -fLo \"{Path(artwork_path, poster_file_path)}\" {src_URL_with_token}"
    else:
        script_line = f"{os.linesep}mkdir -p \"{artwork_path}\" && curl -C - -fLo \"{Path(artwork_path, poster_file_path)}\" {src_URL_with_token}"
    script_string = script_string + f"{script_line}{os.linesep}"

def bar_and_log(the_bar, msg):
    logging.info(msg)
    the_bar.text = msg

def download_file(src_URL, target_path, target_filename):
    p = Path(target_path)
    p.mkdir(parents=True, exist_ok=True)

    dlPath = download(f"{src_URL}", PLEX_TOKEN, filename=target_filename, savepath=target_path)
    rename_by_type(dlPath)

def get_file(src_URL, bar, item, target_path, target_file):
    if src_URL[0] == '/':
        src_URL_with_token = f"{PLEX_URL}{src_URL}?X-Plex-Token={PLEX_TOKEN}"
        src_URL = f"{PLEX_URL}{src_URL}"
        # src_URL_no_token = f"{PLEX_URL}{src_URL}?X-Plex-Token=REDACTED"

    bar_and_log(bar, f"{item.title} - art: {src_URL}")

    if POSTER_DOWNLOAD:
        bar_and_log(bar, f"{item.title} - DOWNLOADING {target_file}")
        download_file(src_URL, target_path, target_file)
    else:
        bar_and_log(bar, f"{item.title} - building download command")
        add_script_line(target_path, target_file, src_URL_with_token)

def item_init(item, the_lib):
    title = item.title
    tmpDict = {}
    item_path, item_name = getPath(the_lib, item)
    dir_name = ""
    msg = ""
    if PLEX_PATHS:
        tgt_dir = Path(f"{POSTER_DIR}{item_path}")
    else:
        if POSTER_CONSOLIDATE:
            tgt_dir = Path(POSTER_DIR, "all_libraries")
        else:
            tgt_dir = Path(POSTER_DIR, lib)

        dir_name, msg = validate_filename(f"collection-{title}")
        logging.info(f"{msg}")

        if not tgt_dir.is_file():
            tgt_dir.mkdir(parents=True, exist_ok=True)

    attempts = 0

    return title, tmpDict, item_path, item_name, dir_name, msg, tgt_dir, attempts, title

for lib in lib_array:
    the_lib = plex.library.section(lib)

    if INCLUDE_COLLECTION_ARTWORK:
        print(f"getting collections from [{lib}]...")

        items = the_lib.collections()
        item_total = len(items)
        print(f"{item_total} collection(s) retrieved...")
        item_count = 1

        tgt_ext = ".dat" if USE_MAGIC else ".jpg"

        if item_total > 0:
            with alive_bar(item_total, dual_line=True, title='Grab Collection Posters') as bar:
                reported_item_status = False
                for item in items:

                    logging.info(f"================================")
                    logging.info(f"Starting {item.title}")

                    title = item.title
                    tmpDict = {}
                    item_count = item_count + 1
                    if POSTER_CONSOLIDATE:
                        tgt_dir = os.path.join(POSTER_DIR, "all_libraries")
                    else:
                        tgt_dir = os.path.join(POSTER_DIR, lib)

                    if not os.path.exists(tgt_dir):
                        os.makedirs(tgt_dir)

                    dir_name, msg = validate_filename(f"collection-{title}")
                    attempts = 0

                    artwork_path = Path(tgt_dir, dir_name)

                    while attempts < 5:
                        try:

                            bar_and_log(bar, f"{title} - getting posters - attempt {attempts}")

                            posters = item.posters()

                            bar_and_log(bar, f"{title} - {len(posters)} posters")

                            import fnmatch

                            count = 0

                            if os.path.exists(artwork_path):
                                count = len(fnmatch.filter(os.listdir(artwork_path), '*.*'))
                                logging.info(f"{count} files in {artwork_path}")

                            posters_to_go = count - POSTER_DEPTH

                            if posters_to_go < 0:
                                poster_to_go = abs(posters_to_go)
                            else:
                                poster_to_go = 0

                            logging.info(f"{poster_to_go} needed to reach depth {POSTER_DEPTH}")

                            no_more_to_get = count >= len(posters)
                            full_for_now = count >= POSTER_DEPTH and POSTER_DEPTH > 0
                            no_point_in_looking = full_for_now or no_more_to_get

                            if not no_point_in_looking:
                                idx = 1
                                for poster in posters:
                                    if POSTER_DEPTH > 0 and idx > POSTER_DEPTH:
                                        bar_and_log(bar, f"Reached max depth of {POSTER_DEPTH}; exiting loop")
                                        break

                                    poster_obj = {}
                                    tgt_file_path = f"collection-{title}-{str(idx).zfill(3)}{tgt_ext}"
                                    final_file_path = os.path.join(artwork_path, tgt_file_path)

                                    poster_obj["folder"] = artwork_path
                                    poster_obj["file"] = tgt_file_path

                                    src_URL = poster.key
                                    if src_URL[0] == '/':
                                        src_URL = f"{PLEX_URL}{poster.key}&X-Plex-Token={PLEX_TOKEN}"
                                        poster_obj["URL"] = src_URL
                                    else:
                                        poster_obj["URL"] = src_URL

                                    bar.text = f"{progress_str} - {idx}"
                                    logging.info(f"--------------------------------")
                                    logging.info(f"processing {progress_str} - {idx}")

                                    if not os.path.exists(final_file_path):
                                        logging.info(f"{final_file_path} does not yet exist")
                                        if POSTER_DOWNLOAD:
                                            p = Path(artwork_path)
                                            p.mkdir(parents=True, exist_ok=True)

                                            logging.info(f"downloading {src_URL}")
                                            logging.info(f"to {tgt_file_path}")
                                            thumbPath = download(f"{src_URL}", PLEX_TOKEN, filename=tgt_file_path, savepath=artwork_path)

                                            rename_by_type(final_file_path, thumbPath)

                                        else:
                                            mkdir_flag = "" if IS_WINDOWS else '-p '
                                            script_line_start = f""
                                            if idx == 1:
                                                script_line_start = f"mkdir {mkdir_flag}\"{dir_name}\"{os.linesep}"

                                            script_line = f"{script_line_start}curl -C - -fLo \"{os.path.join(dir_name, tgt_file_path)}\" \"{src_URL}\""

                                            script_string = script_string + f"{script_line}{os.linesep}"
                                    else:
                                        logging.info(f"{final_file_path} ALREADY EXISTS")

                                    idx += 1
                            else:
                                if not reported_item_status:
                                    logging.info(f"Grabbed all available posters: {no_more_to_get}")
                                    if full_for_now:
                                        logging.info(f"{POSTER_DEPTH} image(s) retrieved already")
                                    logging.info(f"No point is looking anymore: {no_point_in_looking}")
                                    reported_item_status = True


                            attempts = 6
                        except Exception as ex:
                            progress_str = "EX: " + item.title
                            logging.info(progress_str)


                    bar()

                    # Wait between items in case hammering the Plex server turns out badly.
                    time.sleep(DELAY)

    if not ONLY_COLLECTION_ARTWORK:
        print(f"getting {the_lib.type}s from [{lib}]...")
        logging.info(f"getting {the_lib.type}s from [{lib}]...")
        items = plex.library.section(lib).all()
        item_total = len(items)
        logging.info(f"looping over {item_total} items...")
        item_count = 1

        plex_links = []
        external_links = []

        with alive_bar(item_total, dual_line=True, title='Grab all posters') as bar:
            reported_item_status = False
            for item in items:

                logging.info(f"================================")
                logging.info(f"Starting {item.title}")
                imdbid, tmid, tvid = getTID(item.guids)
                tmpDict = {}
                item_count = item_count + 1
                if POSTER_CONSOLIDATE:
                    tgt_dir = os.path.join(POSTER_DIR, "all_libraries")
                else:
                    tgt_dir = os.path.join(POSTER_DIR, lib)

                if not os.path.exists(tgt_dir):
                    os.makedirs(tgt_dir)

                old_dir_name, msg = validate_filename(item.title)
                dir_name, msg = validate_filename(f"{tmid}-{item.title}")
                attempts = 0

                old_path = Path(tgt_dir, old_dir_name)
                artwork_path = Path(tgt_dir, dir_name)

                if os.path.exists(old_path):
                    os.rename(old_path, artwork_path)

                while attempts < 5:
                    try:

                        progress_str = f"{item.title} - getting posters"
                        logging.info(f"{progress_str} - {attempts}")
                        bar.text = progress_str

                        posters = item.posters()

                        progress_str = f"{item.title} - {len(posters)} posters"
                        logging.info(progress_str)
                        bar.text = progress_str

                        import fnmatch

                        count = 0
                        posters_to_go = 0

                        if os.path.exists(artwork_path):
                            count = len(fnmatch.filter(os.listdir(artwork_path), '*.*'))
                            logging.info(f"{count} files in {artwork_path}")

                        posters_to_go = count - POSTER_DEPTH

                        if posters_to_go < 0:
                            poster_to_go = abs(posters_to_go)
                        else:
                            poster_to_go = 0

                        logging.info(f"{poster_to_go} needed to reach depth {POSTER_DEPTH}")

                        no_more_to_get = count >= len(posters)
                        full_for_now = count >= POSTER_DEPTH and POSTER_DEPTH > 0
                        no_point_in_looking = full_for_now or no_more_to_get

                        if not no_point_in_looking:
                            idx = 1
                            for poster in posters:
                                if POSTER_DEPTH > 0 and idx > POSTER_DEPTH:
                                    logging.info(f"Reached max depth of {POSTER_DEPTH}; exiting loop")
                                    break

                                poster_obj = {}
                                tgt_ext = ".dat" if USE_MAGIC else ".jpg"
                                tgt_file_path = f"{tmid}-{tvid}-{item.ratingKey}-{str(idx).zfill(3)}{tgt_ext}"
                                final_file_path = os.path.join(artwork_path, tgt_file_path)

                                poster_obj["folder"] = artwork_path
                                poster_obj["file"] = tgt_file_path

                                src_URL = poster.key
                                if src_URL[0] == '/':
                                    src_URL = f"{PLEX_URL}{poster.key}&X-Plex-Token={PLEX_TOKEN}"
                                    poster_obj["URL"] = src_URL
                                    # plex_links.append(poster_obj)
                                else:
                                    poster_obj["URL"] = src_URL
                                    # external_links.append(poster_obj)

                                bar.text = f"{progress_str} - {idx}"
                                logging.info(f"--------------------------------")
                                logging.info(f"processing {progress_str} - {idx}")

                                if not os.path.exists(final_file_path):
                                    logging.info(f"{final_file_path} does not yet exist")
                                    if POSTER_DOWNLOAD:
                                        p = Path(artwork_path)
                                        p.mkdir(parents=True, exist_ok=True)

                                        logging.info(f"downloading {src_URL}")
                                        logging.info(f"to {tgt_file_path}")
                                        thumbPath = download(f"{src_URL}", PLEX_TOKEN, filename=tgt_file_path, savepath=artwork_path)

                                        rename_by_type(final_file_path, thumbPath)

                                    else:
                                        mkdir_flag = "" if IS_WINDOWS else '-p '
                                        script_line_start = f""
                                        if idx == 1:
                                            script_line_start = f"mkdir {mkdir_flag}\"{dir_name}\"{os.linesep}"

                                        script_line = f"{script_line_start}curl -C - -fLo \"{os.path.join(dir_name, tgt_file_path)}\" \"{src_URL}\""

                                        script_string = script_string + f"{script_line}{os.linesep}"
                                else:
                                    logging.info(f"{final_file_path} ALREADY EXISTS")

                                idx += 1
                        else:
                            if not reported_item_status:
                                logging.info(f"Grabbed all available posters: {no_more_to_get}")
                                if full_for_now:
                                    logging.info(f"{POSTER_DEPTH} image(s) retrieved already")
                                logging.info(f"No point is looking anymore: {no_point_in_looking}")
                                reported_item_status = True

                        attempts = 6
                    except Exception as ex:
                        progress_str = "EX: " + item.title
                        logging.info(progress_str)

                        attempts += 1

                bar()

    progress_str = f"COMPLETE"
    logging.info(progress_str)

    bar.text = progress_str


    print(os.linesep)
    if not POSTER_DOWNLOAD:
        scr_path = os.path.join(tgt_dir, SCRIPT_FILE)
        if len(script_string) > 0:
            with open(scr_path, "w", encoding='utf-8') as myfile:
                myfile.write(f"{script_string}{os.linesep}")
