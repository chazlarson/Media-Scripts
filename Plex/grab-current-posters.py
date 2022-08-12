from dbm.ndbm import library
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

load_dotenv()

logging.basicConfig(filename='grab-current-posters.log', filemode='w', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

logging.info('Starting grab-current-posters.py')

def booler(thing):
    if type(thing) == str:
        thing = eval(thing)
    return bool(thing)

PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')
LIBRARY_NAME = os.getenv('LIBRARY_NAME')
LIBRARY_NAMES = os.getenv('LIBRARY_NAMES')
POSTER_DIR = os.getenv('CURRENT_POSTER_DIR')
POSTER_DEPTH =  int(os.getenv('POSTER_DEPTH'))
POSTER_DOWNLOAD =  booler(os.getenv('POSTER_DOWNLOAD'))
POSTER_CONSOLIDATE =  booler(os.getenv('POSTER_CONSOLIDATE'))
if os.getenv('ARTWORK') is None:
    ARTWORK =  booler(os.getenv('ARTWORK_AND_POSTERS'))
else:
    ARTWORK =  booler(os.getenv('ARTWORK'))
PLEX_PATHS = booler(os.getenv('PLEX_PATHS'))

SCRIPT_FILE = "get_images.sh"
SCRIPT_SEED = f"#!/bin/bash{os.linesep}{os.linesep}# SCRIPT TO GRAB IMAGES{os.linesep}{os.linesep}"
IS_WINDOWS = platform.system() == 'Windows'

if IS_WINDOWS:
    SCRIPT_FILE = "get_images.bat"
    SCRIPT_SEED = f"@echo off{os.linesep}{os.linesep}"


if POSTER_DEPTH is None:
    POSTER_DEPTH = 0

if POSTER_DOWNLOAD:
    script_string = f""
else:
    script_string = SCRIPT_SEED

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

def getPath(library, item, season=False):
    if library.type == 'movie':
        for media in item.media:
            for part in media.parts:
                return part.file.rsplit('/', 1)[0]
    elif library.type == 'show':
        for episode in item.episodes():
            for media in episode.media:
                for part in media.parts:
                    if season:
                        return part.file.rsplit('/', 1)[0]
                    return part.file.rsplit('/', 2)[0]

print(f"connecting to {PLEX_URL}...")
logging.info(f"connecting to {PLEX_URL}...")
plex = PlexServer(PLEX_URL, PLEX_TOKEN)
for lib in lib_array:
    print(f"getting items from [{lib}]...")
    logging.info(f"getting items from [{lib}]...")
    the_lib = plex.library.section(lib)
    items = the_lib.all()
    item_total = len(items)
    logging.info(f"looping over {item_total} items...")
    item_count = 1

    plex_links = []
    external_links = []

    with alive_bar(item_total, dual_line=True, title='Grab current posters') as bar:
        for item in items:
            imdbid, tmid, tvid = getTID(item.guids)
            tmpDict = {}
            item_count = item_count + 1
            item_path = getPath(the_lib, item)

            dir_name = ""

            if PLEX_PATHS:
                tgt_dir = Path(f"{POSTER_DIR}{item_path}")

            else:
                if POSTER_CONSOLIDATE:
                    tgt_dir = os.path.join(POSTER_DIR, "all_libraries")
                else:
                    tgt_dir = os.path.join(POSTER_DIR, lib)

                dir_name, msg = validate_filename(f"{tmid}-{item.title}-{item.year}")

                if not os.path.exists(tgt_dir):
                    os.makedirs(tgt_dir)

            attempts = 0

            progress_str = f"{item.title}"

            bar.text = progress_str

            while attempts < 5:
                try:

                    progress_str = f"{item.title} - Getting poster"
                    logging.info(f"{progress_str} - {attempts}")

                    script_line = ""

                    bar.text = progress_str

                    artwork_path = Path(tgt_dir, f"{dir_name}")

                    poster_src = item.thumb
                    background_src = item.art

                    tgt_ext = ".dat" if USE_MAGIC else ".jpg"

                    if PLEX_PATHS:
                        poster_file_path = f"poster{tgt_ext}"
                        background_file_path = f"background{tgt_ext}"
                    else:
                        file_base = f"{tmid}-{tvid}-{item.ratingKey}"
                        if POSTER_CONSOLIDATE:
                            file_base = f"{file_base}-{lib}"

                        poster_file_path = f"{file_base}{tgt_ext}"
                        background_file_path = f"{file_base}-BG{tgt_ext}"

                    old_poster_file_path = f"{item.ratingKey}.png"


                    final_poster_file_path = os.path.join(artwork_path, poster_file_path)
                    old_final_poster_file_path = os.path.join(artwork_path, old_poster_file_path)

                    final_background_file_path = os.path.join(artwork_path, background_file_path)

                    logging.info(f"final poster path: {final_poster_file_path}")
                    logging.info(f"final background path: {final_background_file_path}")

    # BACKGROUNDS
                    if ARTWORK:
                        progress_str = f"{item.title} - no final art file"
                        logging.info(progress_str)

                        bar.text = progress_str

                        if not os.path.exists(final_background_file_path):
                            progress_str = f"{item.title} - Grabbing art"
                            logging.info(progress_str)

                            bar.text = progress_str

                            src_URL = background_src
                            # '/library/metadata/999083/art/1654180581'
                            src_URL_no_token = src_URL

                            if src_URL is not None:
                                if src_URL[0] == '/':
                                    # src_URL = f"{PLEX_URL}{src_URL}?X-Plex-Token={PLEX_TOKEN}"
                                    src_URL = f"{PLEX_URL}{src_URL}"
                                    # src_URL_no_token = f"{PLEX_URL}{src_URL}?X-Plex-Token=REDACTED"

                                progress_str = f"{item.title} - art: {src_URL}"
                                logging.info(progress_str)

                                bar.text = progress_str

                                if POSTER_DOWNLOAD:
                                    p = Path(artwork_path)
                                    p.mkdir(parents=True, exist_ok=True)

                                    progress_str = f"{item.title} - DOWNLOADING {background_file_path}"
                                    logging.info(progress_str)
                                    bar.text = progress_str

                                    thumbPath = download(f"{src_URL}", PLEX_TOKEN, filename=background_file_path, savepath=artwork_path)

                                    if USE_MAGIC:
                                        p = Path(final_background_file_path)

                                        extension = mimetypes.guess_extension(mime.from_file(thumbPath), strict=False)
                                        if extension == '.html':
                                            p.unlink()
                                        else:
                                            p.rename(p.with_suffix(extension))

                                else:
                                    progress_str = f"{item.title} - building download command"
                                    logging.info(progress_str)
                                    bar.text = progress_str

                                    if IS_WINDOWS:
                                        script_line = f"mkdir \"{dir_name}\"{os.linesep}curl -C - -fLo \"{os.path.join(dir_name, background_file_path)}\" {src_URL}"
                                    else:
                                        script_line = f"mkdir -p \"{dir_name}\" && curl -C - -fLo \"{os.path.join(dir_name, background_file_path)}\" {src_URL}"
                            else:
                                progress_str = f"{item.title} - art is None"
                                logging.info(progress_str)
                                bar.text = progress_str

    # POSTERS
                    if not os.path.exists(final_poster_file_path):
                        progress_str = f"{item.title} - no final file"
                        logging.info(progress_str)

                        bar.text = progress_str

                        if not os.path.exists(old_final_poster_file_path):
                            progress_str = f"{item.title} - Grabbing thumb"

                            bar.text = progress_str

                            src_URL = poster_src
                            # '/library/metadata/2187432/thumb/1652287170'
                            src_URL_no_token = src_URL

                            if src_URL is not None:
                                if src_URL[0] == '/':
                                    # src_URL = f"{PLEX_URL}{src_URL}?X-Plex-Token={PLEX_TOKEN}"
                                    src_URL = f"{PLEX_URL}{src_URL}"
                                    # src_URL_no_token = f"{PLEX_URL}{src_URL}?X-Plex-Token=REDACTED"

                                progress_str = f"{item.title} - thumb: {src_URL}"
                                logging.info(progress_str)

                                bar.text = progress_str

                                if POSTER_DOWNLOAD:
                                    p = Path(artwork_path)
                                    p.mkdir(parents=True, exist_ok=True)

                                    progress_str = f"{item.title} - DOWNLOADING {poster_file_path}"
                                    bar.text = progress_str
                                    logging.info(progress_str)
                                    thumbPath = download(f"{src_URL}", PLEX_TOKEN, filename=poster_file_path, savepath=artwork_path)

                                    if USE_MAGIC:
                                        p = Path(final_poster_file_path)

                                        extension = mimetypes.guess_extension(mime.from_file(thumbPath), strict=False)
                                        if extension == '.html':
                                            p.unlink()
                                        else:
                                            p.rename(p.with_suffix(extension))

                                else:
                                    progress_str = f"{item.title} - building download command"
                                    bar.text = progress_str
                                    logging.info(progress_str)
                                    if IS_WINDOWS:
                                        script_line = script_line + f"{os.linesep}mkdir \"{dir_name}\"{os.linesep}curl -C - -fLo \"{os.path.join(dir_name, poster_file_path)}\" {src_URL}"
                                    else:
                                        script_line = script_line + f"{os.linesep}mkdir -p \"{dir_name}\" && curl -C - -fLo \"{os.path.join(dir_name, poster_file_path)}\" {src_URL}"
                            else:
                                progress_str = f"{item.title} - thumb is None"
                                bar.text = progress_str
                                logging.info(progress_str)
                        else:
                            progress_str = f"{item.title} - RENAMING TO {poster_file_path}"
                            logging.info(progress_str)
                            bar.text = progress_str
                            os.rename(old_final_poster_file_path, final_poster_file_path)

                    attempts = 6
                    script_string = script_string + f"{script_line}{os.linesep}"

                except Exception as ex:
                    bar.text = progress_str
                    logging.error(ex)

                    attempts += 1
            bar()

    print(os.linesep)
    if not POSTER_DOWNLOAD:
        scr_path = os.path.join(tgt_dir, SCRIPT_FILE)
        logging.info(f"writing {scr_path}")
        if len(script_string) > 0:
            with open(scr_path, "w") as myfile:
                myfile.write(f"{script_string}{os.linesep}")
