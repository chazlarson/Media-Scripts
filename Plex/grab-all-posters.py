import logging
import os
import platform
from pathlib import Path

import time

from alive_progress import alive_bar
from dotenv import load_dotenv
from plexapi.exceptions import Unauthorized
from plexapi.server import PlexServer
from plexapi.utils import download
from helpers import booler, getTID, validate_filename

import json
import piexif
import piexif.helper

import filetype
ID_FILES = True

load_dotenv()

logging.basicConfig(
    filename="grab-all-posters.log",
    filemode="w",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logging.info("Starting grab-all-posters.py")

PLEX_URL = os.getenv("PLEX_URL")
PLEX_TOKEN = os.getenv("PLEX_TOKEN")
LIBRARY_NAME = os.getenv("LIBRARY_NAME")
LIBRARY_NAMES = os.getenv("LIBRARY_NAMES")
POSTER_DIR = os.getenv("POSTER_DIR")
POSTER_DEPTH = int(os.getenv("POSTER_DEPTH"))
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

GRAB_SEASONS = booler(os.getenv("GRAB_SEASONS"))
GRAB_EPISODES = booler(os.getenv("GRAB_EPISODES"))

if not DELAY:
    DELAY = 0

if POSTER_DEPTH is None:
    POSTER_DEPTH = 0

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
    lib_array = LIBRARY_NAMES.split(",")
else:
    lib_array = [LIBRARY_NAME]

imdb_str = "imdb://"
tmdb_str = "tmdb://"
tvdb_str = "tvdb://"

print(f"connecting to {PLEX_URL}...")
logging.info(f"connecting to {PLEX_URL}...")
try:
    plex = PlexServer(PLEX_URL, PLEX_TOKEN)
except Unauthorized:
    print("Plex Error: Plex token is invalid")
    exit()
except Exception as ex:
  print(f"Plex Error: {ex.args}")
  exit()

logging.info("connection success")

def get_SE_str(item):
    if item.TYPE == "season":
        ret_val = f"S{str(item.seasonNumber).zfill(2)}"
    elif item.TYPE == "episode":
        ret_val = f"S{str(item.seasonNumber).zfill(2)}E{str(item.episodeNumber).zfill(2)}"
    else:
        ret_val = f""
    
    return ret_val


def get_posters(item, artwork_path, tmid, tvid):
    global SCRIPT_STRING
    attempts = 0
    all_posters = item.posters()

    while attempts < 5:
        try:
            progress_str = f"{get_SE_str(item)} - {item.title} - {len(all_posters)} posters"

            logging.info(progress_str)
            bar.text = progress_str

            import fnmatch

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

                    poster_obj = {}
                    tgt_ext = ".dat" if ID_FILES else ".jpg"
                    if item.TYPE == "season":
                        tgt_file_path = f"{tmid}-{tvid}-{item.ratingKey}-{get_SE_str(item)}{tgt_ext}"
                    elif item.TYPE == "episode":
                        tgt_file_path = f"{tmid}-{tvid}-{item.ratingKey}-{get_SE_str(item)}-{str(idx).zfill(3)}{tgt_ext}"
                    else:
                        tgt_file_path = f"{tmid}-{tvid}-{item.ratingKey}-{str(idx).zfill(3)}{tgt_ext}"
                    final_file_path = os.path.join(
                        artwork_path, tgt_file_path
                    )

                    poster_obj["folder"] = artwork_path
                    poster_obj["file"] = tgt_file_path

                    src_URL = poster.key
                    if src_URL[0] == "/":
                        src_URL = f"{PLEX_URL}{poster.key}&X-Plex-Token={PLEX_TOKEN}"
                        poster_obj["URL"] = src_URL
                        # plex_links.append(poster_obj)
                    else:
                        poster_obj["URL"] = src_URL
                        # external_links.append(poster_obj)

                    bar.text = f"{progress_str} - {idx}"
                    logging.info("--------------------------------")
                    logging.info(f"processing {progress_str} - {idx}")

                    if not os.path.exists(final_file_path):
                        logging.info(
                            f"{final_file_path} does not yet exist"
                        )
                        if POSTER_DOWNLOAD:
                            p = Path(artwork_path)
                            p.mkdir(parents=True, exist_ok=True)

                            logging.info(f"downloading {src_URL}")
                            logging.info(f"to {tgt_file_path}")
                            thumbPath = download(
                                f"{src_URL}",
                                PLEX_TOKEN,
                                filename=tgt_file_path,
                                savepath=artwork_path,
                            )
                            logging.info(f"Downloaded {thumbPath}")

                            # local_file = str(rename_by_type(final_file_path))
                            # Write out exif data
                            # load existing exif data from image
                            # exif_dict = piexif.load(local_file)
                            # # insert custom data in usercomment field
                            # exif_dict["Exif"][piexif.ExifIFD.UserComment] = piexif.helper.UserComment.dump(
                            #     "PMM WAS HERE",
                            #     encoding="unicode"
                            # )
                            # # insert mutated data (serialised into JSON) into image
                            # piexif.insert(
                            #     piexif.dump(exif_dict),
                            #     local_file
                            # )

                        else:
                            mkdir_flag = "" if IS_WINDOWS else "-p "
                            script_line_start = ""
                            if idx == 1:
                                script_line_start = f'mkdir {mkdir_flag}"{artwork_path}"{os.linesep}'

                            script_line = f'{script_line_start}curl -C - -fLo "{os.path.join(artwork_path, tgt_file_path)}" "{src_URL}"'

                            SCRIPT_STRING = (
                                SCRIPT_STRING + f"{script_line}{os.linesep}"
                            )
                    else:
                        logging.info(f"{final_file_path} ALREADY EXISTS")

                    idx += 1

            attempts = 6
        except Exception as ex:
            progress_str = f"EX: {ex} {item.title}"
            logging.info(progress_str)

            attempts  += 1


def rename_by_type(target):
    p = Path(target)

    kind = filetype.guess(target)
    if kind is None:
        print('Cannot guess file type; assuming jpg')
        extension = ".jpg"
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
        # src_URL_no_token = f"{PLEX_URL}{src_URL}?X-Plex-Token=REDACTED"

    bar_and_log(bar, f"{item.title} - art: {src_URL}")

    if POSTER_DOWNLOAD:
        bar_and_log(bar, f"{item.title} - DOWNLOADING {target_file}")
        download_file(src_URL, target_path, target_file)
    else:
        bar_and_log(bar, f"{item.title} - building download command")
        SCRIPT_STRING += add_script_line(target_path, target_file, src_URL_with_token)


for lib in lib_array:
    
    try:
        the_lib = plex.library.section(lib)

        if INCLUDE_COLLECTION_ARTWORK:
            print(f"getting collections from [{lib}]...")

            items = the_lib.collections()
            item_total = len(items)
            print(f"{item_total} collection(s) retrieved...")
            item_count = 1

            tgt_ext = ".dat"

            if item_total > 0:
                with alive_bar(
                    item_total, dual_line=True, title="Grab Collection Posters"
                ) as bar:
                    for item in items:

                        logging.info("================================")
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
                        
                        get_posters(item, artwork_path, tmid, tvid)

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

            with alive_bar(item_total, dual_line=True, title="Grab all posters") as bar:
                for item in items:

                    logging.info("================================")
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

                    get_posters(item, artwork_path, tmid, tvid)

                    if item.TYPE == "show":
                        if GRAB_SEASONS:
                            # get seasons
                            seasons = item.seasons()
 
                            # loop over all:
                            for s in seasons:
                                season_artwork_path = Path(artwork_path, f"{get_SE_str(s)}-{s.title}")
                                get_posters(s, season_artwork_path, tmid, tvid)
                                if GRAB_EPISODES:
                                    # get episodes
                                    episodes = s.episodes()

                                    # loop over all
                                    for e in episodes:
                                        episode_artwork_path = Path(season_artwork_path, f"{get_SE_str(e)}-{e.title}")
                                        get_posters(e, episode_artwork_path, tmid, tvid)

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


# %%
