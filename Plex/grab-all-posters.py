import logging
import mimetypes
import os
import platform
import sys
import textwrap
from pathlib import Path, PurePath
from xmlrpc.client import Boolean

USE_MAGIC = True
try:
    import magic
except:
    print("Can't import the python-magic library")
    print("This typically means you haven't installed libmagic")
    print("This script will assume all images are JPEG format")
    USE_MAGIC = False
import requests
from alive_progress import alive_bar
from dotenv import load_dotenv
from pathvalidate import is_valid_filename, sanitize_filename
from plexapi.server import PlexServer
from plexapi.utils import download
from tmdbapis import TMDbAPIs

logging.basicConfig(filename='grab-all-posters.log', filemode='w', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

logging.info('Starting grab-all-posters.py')

load_dotenv()

PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')
LIBRARY_NAME = os.getenv('LIBRARY_NAME')
LIBRARY_NAMES = os.getenv('LIBRARY_NAMES')
POSTER_DIR = os.getenv('POSTER_DIR')
POSTER_DEPTH =  int(os.getenv('POSTER_DEPTH'))
POSTER_DOWNLOAD =  Boolean(os.getenv('POSTER_DOWNLOAD'))
POSTER_CONSOLIDATE =  Boolean(os.getenv('POSTER_CONSOLIDATE'))

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

def getTID(theList):
    imdbid = None
    tmid = None
    tvid = None
    for guid in theList:
        if imdb_str in guid.id:
            imdid = guid.id.replace(imdb_str,'')
        if tmdb_str in guid.id:
            tmid = guid.id.replace(tmdb_str,'')
        if tvdb_str in guid.id:
            tvid = guid.id.replace(tvdb_str,'')
    return imdbid, tmid, tvid

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
    logging.info(f"looping over {item_total} items...")
    item_count = 1

    plex_links = []
    external_links = []

    with alive_bar(item_total, dual_line=True, title='Grab all posters') as bar:
        for item in items:
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

                    if os.path.exists(artwork_path):
                        count = len(fnmatch.filter(os.listdir(artwork_path), '*.*'))

                    no_more_to_get = count >= len(posters)
                    full_for_now = count >= POSTER_DEPTH and POSTER_DEPTH > 0
                    no_point_in_looking = full_for_now or no_more_to_get

                    if not no_point_in_looking:
                        idx = 1
                        for poster in posters:
                            if POSTER_DEPTH > 0 and idx > POSTER_DEPTH:
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
                            logging.info(progress_str)

                            if not os.path.exists(final_file_path):
                                if POSTER_DOWNLOAD:
                                    p = Path(artwork_path)
                                    p.mkdir(parents=True, exist_ok=True)

                                    thumbPath = download(f"{src_URL}", PLEX_TOKEN, filename=tgt_file_path, savepath=artwork_path)

                                    if USE_MAGIC:
                                        p = Path(final_file_path)

                                        extension = mimetypes.guess_extension(mime.from_file(thumbPath), strict=False)
                                        p.rename(p.with_suffix(extension))
                                else:
                                    mkdir_flag = "" if IS_WINDOWS else '-p '
                                    script_line_start = f""
                                    if idx == 1:
                                        script_line_start = f"mkdir {mkdir_flag}\"{dir_name}\"{os.linesep}"

                                    script_line = f"{script_line_start}curl -C - -fLo \"{os.path.join(dir_name, tgt_file_path)}\" \"{src_URL}\""

                                    script_string = script_string + f"{script_line}{os.linesep}"

                            idx += 1
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
            with open(scr_path, "w") as myfile:
                myfile.write(f"{script_string}{os.linesep}")
