from xmlrpc.client import Boolean
from plexapi.server import PlexServer
from plexapi.utils import download
import os
from dotenv import load_dotenv
import sys
import textwrap
from tmdbapis import TMDbAPIs
import requests
from pathlib import Path, PurePath
from pathvalidate import is_valid_filename, sanitize_filename
import logging
import platform

load_dotenv()

logging.basicConfig(filename='grab-current-posters.log', filemode='w', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

logging.info('Starting grab-current-posters.py')

PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')
LIBRARY_NAME = os.getenv('LIBRARY_NAME')
LIBRARY_NAMES = os.getenv('LIBRARY_NAMES')
POSTER_DIR = os.getenv('CURRENT_POSTER_DIR')
POSTER_DEPTH =  int(os.getenv('POSTER_DEPTH'))
POSTER_DOWNLOAD =  Boolean(int(os.getenv('POSTER_DOWNLOAD')))
POSTER_CONSOLIDATE =  Boolean(int(os.getenv('POSTER_CONSOLIDATE')))
ARTWORK_AND_POSTER =  Boolean(int(os.getenv('ARTWORK_AND_POSTER')))

SCRIPT_FILE = "get_images.sh”
SCRIPT_SEED = f"#!/bin/bash{os.linesep}{os.linesep}# SCRIPT TO GRAB IMAGES{os.linesep}{os.linesep}"
IS_WINDOWS = platform.system() == 'Windows'

if IS_WINDOWS:
    SCRIPT_FILE = "get_images.bat”
    SCRIPT_SEED = f"@echo off{os.linesep}{os.linesep}"


if POSTER_DEPTH is None:
    POSTER_DEPTH = 0

if LIBRARY_NAMES:
    lib_array = LIBRARY_NAMES.split(",")
else:
    lib_array = [LIBRARY_NAME]

tmdb_str = 'tmdb://'
tvdb_str = 'tvdb://'

def getTID(theList):
    tmid = None
    tvid = None
    for guid in theList:
        if tmdb_str in guid.id:
            tmid = guid.id.replace(tmdb_str,'')
        if tvdb_str in guid.id:
            tvid = guid.id.replace(tvdb_str,'')
    return tmid, tvid

def progress(count, total, status=''):
    bar_len = 40
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)
    stat_str = textwrap.shorten(status, width=80)

    sys.stdout.write('[%s] %s%s ... %s\r' % (bar, percents, '%', stat_str.ljust(80)))
    sys.stdout.flush()

def validate_filename(filename):
    if is_valid_filename(filename):
        return filename, None
    else:
        mapping_name = sanitize_filename(filename)
        stat_string = f"Log Folder Name: {filename} is invalid using {mapping_name}"
        logging.info(stat_string)
        return mapping_name, stat_string

print(f"connecting to {PLEX_URL}...")
logging.info(f"connecting to {PLEX_URL}...")
plex = PlexServer(PLEX_URL, PLEX_TOKEN)
for lib in lib_array:
    print(f"getting items from [{lib}]...")
    logging.info(f"getting items from [{lib}]...")
    items = plex.library.section(lib).all()
    item_total = len(items)
    print(f"looping over {item_total} items...")
    logging.info(f"looping over {item_total} items...")
    item_count = 1

    plex_links = []
    external_links = []
    if POSTER_DOWNLOAD:
        script_string = f""
    else:
        script_string = SCRIPT_SEED

    for item in items:
        tmdb_id, tvdb_id = getTID(item.guids)
        tmpDict = {}
        item_count = item_count + 1
        if POSTER_CONSOLIDATE:
            tgt_dir = os.path.join(POSTER_DIR, "all_libraries")
        else:
            tgt_dir = os.path.join(POSTER_DIR, lib)
        dir_name, msg = validate_filename(f"{tmdb_id}-{item.title}-{item.year}")
        attempts = 0

        progress_str = f"{item.title}"

        progress(item_count, item_total, progress_str)

        while attempts < 5:
            try:

                progress_str = f"{item.title} - attempt {attempts}"
                logging.info(progress_str)

                script_line = ""

                progress(item_count, item_total, progress_str)

                artwork_path = Path(tgt_dir, f"{dir_name}")
                if POSTER_CONSOLIDATE:
                    poster_file_path = f"{tmdb_id}-{tvdb_id}-{item.ratingKey}-{lib}.png"
                    background_file_path = f"{tmdb_id}-{tvdb_id}-{item.ratingKey}-BG-{lib}.png"
                else:
                    poster_file_path = f"{tmdb_id}-{tvdb_id}-{item.ratingKey}.png"
                    background_file_path = f"{tmdb_id}-{tvdb_id}-{item.ratingKey}-BG.png"
                old_poster_file_path = f"{item.ratingKey}.png"


                final_poster_file_path = os.path.join(artwork_path, poster_file_path)
                old_final_poster_file_path = os.path.join(artwork_path, old_poster_file_path)
                final_background_file_path = os.path.join(artwork_path, background_file_path)

                logging.info(f"final poster path: {final_poster_file_path}")
                logging.info(f"final artwork path: {final_background_file_path}")

# BACKGROUNDS
                if ARTWORK_AND_POSTER:
                    progress_str = f"{item.title} - no final art file"
                    logging.info(progress_str)

                    progress(item_count, item_total, progress_str)

                    if not os.path.exists(final_background_file_path):
                        progress_str = f"{item.title} - Grabbing art"
                        logging.info(progress_str)

                        progress(item_count, item_total, progress_str)

                        src_URL = item.artUrl
                        # '/library/metadata/999083/art/1654180581'
                        src_URL_no_token = src_URL

                        if src_URL is not None:
                            if src_URL[0] == '/':
                                src_URL = f"{PLEX_URL}{src_URL}?X-Plex-Token={PLEX_TOKEN}"
                                src_URL_no_token = f"{PLEX_URL}{src_URL}?X-Plex-Token=REDACTED"

                            progress_str = f"{item.title} - art: {src_URL_no_token}"
                            logging.info(progress_str)

                            progress(item_count, item_total, progress_str)

                            if POSTER_DOWNLOAD:
                                p = Path(artwork_path)
                                p.mkdir(parents=True, exist_ok=True)

                                progress_str = f"{item.title} - DOWNLOADING {background_file_path}"
                                logging.info(progress_str)
                                progress(item_count, item_total, progress_str)
                                thumbPath = download(f"{src_URL}", PLEX_TOKEN, filename=background_file_path, savepath=artwork_path)
                            else:
                                progress_str = f"{item.title} - building download command"
                                logging.info(progress_str)
                                progress(item_count, item_total, progress_str)

                                script_line = f"mkdir -p \"{dir_name}\" && curl -C - -fLo \"{os.path.join(dir_name, background_file_path)}\" {src_URL}"
                        else:
                            progress_str = f"{item.title} - art is None"
                            logging.info(progress_str)
                            progress(item_count, item_total, progress_str)

# POSTERS
                if not os.path.exists(final_poster_file_path):
                    progress_str = f"{item.title} - no final file"
                    logging.info(progress_str)

                    progress(item_count, item_total, progress_str)

                    if not os.path.exists(old_final_poster_file_path):
                        progress_str = f"{item.title} - Grabbing thumb"

                        progress(item_count, item_total, progress_str)

                        src_URL = item.thumbUrl
                        # '/library/metadata/2187432/thumb/1652287170'
                        src_URL_no_token = src_URL

                        if src_URL is not None:
                            if src_URL[0] == '/':
                                src_URL = f"{PLEX_URL}{src_URL}?X-Plex-Token={PLEX_TOKEN}"
                                src_URL_no_token = f"{PLEX_URL}{src_URL}?X-Plex-Token=REDACTED"

                            progress_str = f"{item.title} - thumb: {src_URL_no_token}"
                            logging.info(progress_str)

                            progress(item_count, item_total, progress_str)

                            if POSTER_DOWNLOAD:
                                p = Path(artwork_path)
                                p.mkdir(parents=True, exist_ok=True)

                                progress_str = f"{item.title} - DOWNLOADING {poster_file_path}"
                                progress(item_count, item_total, progress_str)
                                logging.info(progress_str)
                                thumbPath = download(f"{src_URL}", PLEX_TOKEN, filename=poster_file_path, savepath=artwork_path)
                            else:
                                progress_str = f"{item.title} - building download command"
                                progress(item_count, item_total, progress_str)
                                logging.info(progress_str)
                                script_line = script_line + f"{os.linesep}mkdir -p \"{dir_name}\" && curl -C - -fLo \"{os.path.join(dir_name, poster_file_path)}\" {src_URL}"
                        else:
                            progress_str = f"{item.title} - thumb is None"
                            progress(item_count, item_total, progress_str)
                            logging.info(progress_str)
                    else:
                        progress_str = f"{item.title} - RENAMING TO {poster_file_path}"
                        logging.info(progress_str)
                        progress(item_count, item_total, progress_str)
                        os.rename(old_final_poster_file_path, final_poster_file_path)

                attempts = 6
                script_string = script_string + f"{script_line}{os.linesep}"

            except Exception as ex:
                progress(item_count, item_total, "EX: " + item.title)
                logging.error(ex)

                attempts += 1

    print(os.linesep)
    if not POSTER_DOWNLOAD:
        scr_path = os.path.join(tgt_dir, SCRIPT_FILE)
        logging.info(f"writing {scr_path}")
        if len(script_string) > 0:
            with open(scr_path, "w") as myfile:
                myfile.write(f"{script_string}{os.linesep}")
