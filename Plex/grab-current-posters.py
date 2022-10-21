import logging
import mimetypes
import os
import platform
from pathlib import Path

from alive_progress import alive_bar
from dotenv import load_dotenv
from plexapi.server import PlexServer
from plexapi.exceptions import Unauthorized
from plexapi.utils import download
from helpers import booler, getTID, validate_filename, getPath

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


load_dotenv()

logging.basicConfig(
    filename="grab-current-posters.log",
    filemode="w",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logging.info("Starting grab-current-posters.py")

PLEX_URL = os.getenv("PLEX_URL")
PLEX_TOKEN = os.getenv("PLEX_TOKEN")
LIBRARY_NAME = os.getenv("LIBRARY_NAME")
LIBRARY_NAMES = os.getenv("LIBRARY_NAMES")
POSTER_DIR = os.getenv("CURRENT_POSTER_DIR")
POSTER_DEPTH = int(os.getenv("POSTER_DEPTH"))
POSTER_DOWNLOAD = booler(os.getenv("POSTER_DOWNLOAD"))
if not POSTER_DOWNLOAD:
    print("================== ATTENTION ==================")
    print("Downloading disabled; file identification not possible")
    print("Script will default to .jpg extension on all images")
    print("================== ATTENTION ==================")
    USE_MAGIC = False

POSTER_CONSOLIDATE = booler(os.getenv("POSTER_CONSOLIDATE"))
if os.getenv("ARTWORK") is None:
    ARTWORK = booler(os.getenv("ARTWORK_AND_POSTER"))
else:
    ARTWORK = booler(os.getenv("ARTWORK"))
PLEX_PATHS = booler(os.getenv("PLEX_PATHS"))

NAME_IN_TITLE = booler(os.getenv("NAME_IN_TITLE"))
POSTER_NAME = os.getenv("POSTER_NAME")
BACKGROUND_NAME = os.getenv("BACKGROUND_NAME")

INCLUDE_COLLECTION_ARTWORK = booler(os.getenv("INCLUDE_COLLECTION_ARTWORK"))

ONLY_COLLECTION_ARTWORK = booler(os.getenv("ONLY_COLLECTION_ARTWORK"))

DELAY = int(os.getenv("DELAY"))

if not DELAY:
    DELAY = 0

SCRIPT_FILE = "get_images.sh"
SCRIPT_SEED = f"#!/bin/bash{os.linesep}{os.linesep}# SCRIPT TO GRAB IMAGES{os.linesep}{os.linesep}"
IS_WINDOWS = platform.system() == "Windows"

if IS_WINDOWS:
    SCRIPT_FILE = "get_images.bat"
    SCRIPT_SEED = f"@echo off{os.linesep}setlocal enableextensions enabledelayedexpansion{os.linesep}{os.linesep}"

if POSTER_DEPTH is None:
    POSTER_DEPTH = 0

if POSTER_DOWNLOAD:
    script_string = ""
else:
    script_string = SCRIPT_SEED

if LIBRARY_NAMES:
    lib_array = LIBRARY_NAMES.split(",")
else:
    lib_array = [LIBRARY_NAME]

if USE_MAGIC:
    mime = magic.Magic(mime=True)

print(f"connecting to {PLEX_URL}...")
logging.info(f"connecting to {PLEX_URL}...")
try:
    plex = PlexServer(PLEX_URL, PLEX_TOKEN)
except Unauthorized:
    print("Plex Error: Plex token is invalid")
    exit()

logging.info("connection success")


def rename_by_type(target):
    p = Path(target)

    if USE_MAGIC:
        logging.info(f"determining file type of {target}")
        extension = mimetypes.guess_extension(mime.from_file(target), strict=False)
    else:
        logging.info(f"no libmagic; assuming {extension}")
        extension = ".jpg"

    if "html" in extension:
        logging.info(f"deleting html file {p}")
        p.unlink()
    else:
        logging.info(f"changing file extension to {extension}")
        p.rename(p.with_suffix(extension))


def add_script_line(artwork_path, poster_file_path, src_URL_with_token):
    if IS_WINDOWS:
        script_line = f'{os.linesep}mkdir "{artwork_path}"{os.linesep}curl -C - -fLo "{Path(artwork_path, poster_file_path)}" {src_URL_with_token}'
    else:
        script_line = f'{os.linesep}mkdir -p "{artwork_path}" && curl -C - -fLo "{Path(artwork_path, poster_file_path)}" {src_URL_with_token}'
    script_string = script_string + f"{script_line}{os.linesep}"


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
            with alive_bar(
                item_total, dual_line=True, title="Grab Collection Posters"
            ) as bar:
                for item in items:

                    logging.info("================================")
                    bar_and_log(bar, f"Starting {item.title}")

                    (
                        title,
                        tmpDict,
                        item_path,
                        item_name,
                        dir_name,
                        msg,
                        tgt_dir,
                        attempts,
                        progress_str,
                    ) = item_init(item, the_lib)

                    item_count = item_count + 1

                    poster_src = item.thumb
                    background_src = item.art

                    artwork_path = Path(tgt_dir, f"{dir_name}")

                    poster_file_path = f"{POSTER_NAME}{tgt_ext}"
                    background_file_path = f"{BACKGROUND_NAME}{tgt_ext}"

                    if not PLEX_PATHS:
                        file_base = f"collection-{title}"
                        if POSTER_CONSOLIDATE:
                            file_base = f"{file_base}-{lib}"
                        poster_file_path = f"{file_base}-{poster_file_path}"
                        background_file_path = f"{file_base}-{background_file_path}"

                    if NAME_IN_TITLE:
                        poster_file_path = f"{item_name}-{poster_file_path}"
                        background_file_path = f"{item_name}-{background_file_path}"

                    while attempts < 5:
                        try:

                            bar_and_log(
                                bar,
                                f"{title} - Getting poster - attempt {attempts + 1}",
                            )

                            script_line = ""

                            if ARTWORK:
                                bar_and_log(
                                    bar, f"{item.title} - grabbing background artwork"
                                )

                                if not Path(
                                    artwork_path, background_file_path
                                ).is_file():
                                    bar_and_log(
                                        bar,
                                        f"{item.title} - Grabbing background artwork",
                                    )

                                    src_URL = background_src

                                    src_URL_no_token = src_URL

                                    if src_URL is not None:
                                        get_file(
                                            src_URL,
                                            bar,
                                            item,
                                            artwork_path,
                                            background_file_path,
                                        )
                                    else:
                                        bar_and_log(bar, f"{item.title} - art is None")

                            # POSTERS
                            if not Path(artwork_path, poster_file_path).is_file():
                                bar_and_log(
                                    bar,
                                    f"{item.title} - no final file - Grabbing thumb",
                                )

                                src_URL = poster_src
                                # '/library/metadata/2187432/thumb/1652287170'
                                src_URL_no_token = src_URL

                                if src_URL is not None:
                                    get_file(
                                        src_URL,
                                        bar,
                                        item,
                                        artwork_path,
                                        poster_file_path,
                                    )
                                else:
                                    bar_and_log(bar, f"{item.title} - thumb is None")

                            attempts = 6

                        except Exception as ex:
                            bar.text = "EXCEPTION"
                            logging.error(ex)

                            attempts += 1
                    bar()

    if not ONLY_COLLECTION_ARTWORK:
        print(f"getting {the_lib.type}s from [{lib}]...")
        logging.info(f"getting {the_lib.type}s from [{lib}]...")
        the_lib = plex.library.section(lib)
        items = the_lib.all()
        item_total = len(items)
        print(f"{item_total} {the_lib.type}s retrieved...")
        item_count = 1

        plex_links = []
        external_links = []
        if item_total > 0:
            with alive_bar(
                item_total, dual_line=True, title="Grab current posters"
            ) as bar:
                for item in items:
                    logging.info("================================")
                    logging.info(f"Starting {item.title}")

                    imdbid, tmid, tvid = getTID(item.guids)
                    tmpDict = {}
                    item_count = item_count + 1
                    item_path, item_name = getPath(the_lib, item)

                    dir_name = ""

                    if PLEX_PATHS:
                        tgt_dir = Path(f"{POSTER_DIR}{item_path}")

                    else:
                        if POSTER_CONSOLIDATE:
                            tgt_dir = Path(POSTER_DIR, "all_libraries")
                        else:
                            tgt_dir = Path(POSTER_DIR, lib)

                        dir_name, msg = validate_filename(
                            f"{tmid}-{item.title}-{item.year}"
                        )
                        if msg is not None:
                            logging.info(f"{dir_name}")
                            logging.info(f"{msg}")

                        if not tgt_dir.is_file():
                            tgt_dir.mkdir(parents=True, exist_ok=True)

                    attempts = 0

                    bar.text = f"{item.title}"

                    while attempts < 5:
                        try:

                            bar_and_log(
                                bar, f"{item.title} - Getting poster - {attempts}"
                            )

                            script_line = ""

                            artwork_path = Path(tgt_dir, f"{dir_name}")

                            poster_src = item.thumb
                            background_src = item.art

                            tgt_ext = ".dat" if USE_MAGIC else ".jpg"

                            poster_file_path = f"{POSTER_NAME}{tgt_ext}"
                            background_file_path = f"{BACKGROUND_NAME}{tgt_ext}"

                            if not PLEX_PATHS:
                                file_base = f"{tmid}-{tvid}-{item.ratingKey}"
                                if POSTER_CONSOLIDATE:
                                    file_base = f"{file_base}-{lib}"
                                poster_file_path = f"{file_base}-{poster_file_path}"
                                background_file_path = (
                                    f"{file_base}-{background_file_path}"
                                )

                            if NAME_IN_TITLE:
                                poster_file_path = f"{item_name}-{poster_file_path}"
                                background_file_path = (
                                    f"{item_name}-{background_file_path}"
                                )

                            # BACKGROUNDS
                            if ARTWORK:
                                bar_and_log(bar, f"{item.title} - no final art file")

                                if not Path(
                                    artwork_path, background_file_path
                                ).is_file():
                                    bar_and_log(bar, f"{item.title} - Grabbing art")

                                    src_URL = background_src
                                    # '/library/metadata/999083/art/1654180581'
                                    src_URL_no_token = src_URL

                                    if src_URL is not None:
                                        get_file(
                                            src_URL,
                                            bar,
                                            item,
                                            artwork_path,
                                            background_file_path,
                                        )
                                    else:
                                        bar_and_log(bar, f"{item.title} - art is None")

                            # POSTERS
                            if not Path(artwork_path, poster_file_path).is_file():
                                bar_and_log(
                                    bar,
                                    f"{item.title} - no final file - Grabbing thumb",
                                )

                                src_URL = poster_src
                                # '/library/metadata/2187432/thumb/1652287170'
                                src_URL_no_token = src_URL

                                if src_URL is not None:
                                    get_file(
                                        src_URL,
                                        bar,
                                        item,
                                        artwork_path,
                                        poster_file_path,
                                    )
                                else:
                                    bar_and_log(bar, f"{item.title} - thumb is None")

                            attempts = 6

                        except Exception as ex:
                            bar.text = "EXCEPTION"
                            logging.error(ex)

                            attempts += 1
                    bar()

    print(os.linesep)
    if not POSTER_DOWNLOAD:
        scr_path = Path(POSTER_DIR, lib.replace(" ", "") + "-" + SCRIPT_FILE)
        bar_and_log(bar, f"writing {scr_path}")
        if len(script_string) > 0:
            with open(scr_path, "w", encoding="utf-8") as myfile:
                myfile.write(f"{script_string}{os.linesep}")
