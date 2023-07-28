from alive_progress import alive_bar
from plexapi.server import PlexServer
from plexapi.exceptions import Unauthorized
import logging
import os
from dotenv import load_dotenv
from tmdbapis import TMDbAPIs
import requests
import pathlib
from pathlib import Path
import platform
from timeit import default_timer as timer
import time
import validators
import random

from helpers import booler, get_all_from_library, get_ids, get_plex, load_and_upgrade_env

# import tvdb_v4_official

start = timer()

import logging
from pathlib import Path
from datetime import datetime, timedelta
# current dateTime
now = datetime.now()

# convert to string
RUNTIME_STR = now.strftime("%Y-%m-%d %H:%M:%S")

SCRIPT_NAME = Path(__file__).stem

VERSION = "0.1.0"

env_file_path = Path(".env")

logging.basicConfig(
    filename=f"{SCRIPT_NAME}.log",
    filemode="w",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logging.info(f"Starting {SCRIPT_NAME}")
print(f"Starting {SCRIPT_NAME}")

status = load_and_upgrade_env(env_file_path)

LIBRARY_NAME = os.getenv("LIBRARY_NAME")
LIBRARY_NAMES = os.getenv("LIBRARY_NAMES")
TMDB_KEY = os.getenv("TMDB_KEY")
TVDB_KEY = os.getenv("TVDB_KEY")
TARGET_LABELS = os.getenv("TARGET_LABELS")
TRACK_RESET_STATUS = booler(os.getenv("TRACK_RESET_STATUS"))
CLEAR_RESET_STATUS = booler(os.getenv("CLEAR_RESET_STATUS", ))

RETAIN_RESET_STATUS_FILE = os.getenv("RETAIN_RESET_STATUS_FILE")
REMOVE_LABELS = booler(os.getenv("REMOVE_LABELS"))
RESET_SEASONS = booler(os.getenv("RESET_SEASONS"))
RESET_EPISODES = booler(os.getenv("RESET_EPISODES"))
RESET_SEASONS_WITH_SERIES = booler(os.getenv("RESET_SEASONS_WITH_SERIES"))
LOCAL_RESET_ARCHIVE = booler(os.getenv("LOCAL_RESET_ARCHIVE"))
DRY_RUN = booler(os.getenv("DRY_RUN"))
FLUSH_STATUS_AT_START = booler(os.getenv("FLUSH_STATUS_AT_START"))

DELAY = 0
try:
    DELAY = int(os.getenv("DELAY"))
except:
    DELAY = 0

if TARGET_LABELS:
    LBL_ARRAY = TARGET_LABELS.split(",")
else:
    LBL_ARRAY = ["xy22y1973"]

if LIBRARY_NAMES:
    LIB_ARRAY = LIBRARY_NAMES.split(",")
else:
    LIB_ARRAY = [LIBRARY_NAME]

IS_WINDOWS = platform.system() == "Windows"

# Commented out until this doesn't throw a 400
# tvdb = tvdb_v4_official.TVDB(TVDB_KEY)

tmdb = TMDbAPIs(TMDB_KEY, language="en")

local_dir = os.path.join(os.getcwd(), "posters")

os.makedirs(local_dir, exist_ok=True)

show_dir = os.path.join(os.getcwd(), "shows")
movie_dir = os.path.join(os.getcwd(), "movies")

os.makedirs(show_dir, exist_ok=True)
os.makedirs(movie_dir, exist_ok=True)

def bar_and_log(the_bar, msg):
    logging.info(msg)
    the_bar.text = msg

def print_and_log(msg):
    logging.info(msg)
    print(msg)

def localFilePath(tgt_dir, rating_key):
    for ext in ["jpg", "png"]:
        local_file = os.path.join(tgt_dir, f"{library_item.ratingKey}.{ext}")
        if os.path.exists(local_file):
            return local_file
    return None


print("tmdb config...")

base_url = tmdb.configuration().secure_base_image_url
size_str = "original"

plex = get_plex()

logging.info("connection success")

if LIBRARY_NAMES == 'ALL_LIBRARIES':
    LIB_ARRAY = []
    all_libs = plex.library.sections()
    for lib in all_libs:
        if lib.type == 'movie' or lib.type == 'show':
            LIB_ARRAY.append(lib.title.strip())

def sleep_for_a_while():
    sleeptime = DELAY
    if DELAY == 99:
        sleeptime = random.uniform(0, 1)
    
    time.sleep(sleeptime)

def plex_knows_this_image(item, source, path):
    logging.info(f"Retrieving posters for Plex {item.type}: {item.title} ")
    # item.reload()
    attempts = 0
    while attempts < 5:
        try:
            list_of_posters = item.posters()
            sleep_for_a_while()
            logging.info(f"Checking {len(list_of_posters)} posters")
            for poster in list_of_posters:
                if poster.provider == source:
                    if poster.key == path:
                        logging.info(f"This is one of Plex' posters: {posterURL}")
                        return poster
            attempts = 6
        except Exception as ex:
            logging.info(f'Exception processing "{item}": {ex}')
            attempts += 1

    return None

def get_tmdb_item(tmdb_id, tvdb_id):
    tmdb_item = None

    if tmdb_id is None and tvdb_id is None:
        return tmdb_item

    if library_item.TYPE == "show":
        if tmdb_id is not None:
            logging.info(f"{item_title}: tmdb_id: {tmdb_id} - getting tv_show")
            tmdb_item = tmdb.tv_show(tmdb_id)
            logging.info(f"{item_title}: tmdb_id: {tmdb_id} - FOUND {tmdb_item.title}")
        else:
            logging.info(f"{item_title}: no tmdb_id, trying tvdb_id")
            if tvdb_id is not None:
                logging.info(f"{item_title}: tvdb_id: {tvdb_id} - SEARCHING FOR tv_show")
                tmdb_search = (
                    tmdb.find_by_id(tvdb_id=tvdb_id)
                )
                if len(tmdb_search.tv_results) > 0:
                    tmdb_item = tmdb_search.tv_results[0]
                    logging.info(f"{item_title}: tvdb_id: {tvdb_id} - FOUND {tmdb_item.title}")
            else:
                logging.info(f"{item_title}: no tvdb_id specified")

                
    else:
        if tmdb_id is not None:
            logging.info(f"{item_title}: tmdb_id: {tmdb_id} - getting movie")
            tmdb_item = tmdb.movie(tmdb_id)
            logging.info(f"{item_title}: tmdb_id: {tmdb_id} - FOUND {tmdb_item.title}")

    return tmdb_item

def get_base_tmdb_image(item_title, tmdb_id):
    tmdb_base = None

    logging.info(f"{item_title}: tmdb_id: {tmdb_id} - NO LOCAL FILE")
    try:
        logging.info(f"{item_title}: tmdb_id: {tmdb_id} - RELOADING ITEM")
        tmdb_item.reload()
        tmdb_base = tmdb_item.poster_path
    except Exception as ex:
        logging.info(f"{item_title}: tmdb_id: {tmdb_id} - EXCEPTION {ex}")
        tmdb_base = None

    return tmdb_base

def set_or_upload_image(bar, item, plex_poster, local_source):
    if plex_poster is not None:
        bar_and_log(bar, f"-> SETTING poster for {item.type} {item.title} to {plex_poster.key}")
        item.setPoster(plex_poster)
    else:
        bar_and_log(bar, f"-> UPLOADING poster for {item.type} {item.title} from {local_source}")
        if not DRY_RUN:
            if not validators.url(local_source):
                logging.info(f"{local_source}: appears to be a file")
                item.uploadPoster(filepath=local_source)
            else:
                logging.info(f"{local_source}: appears to be a URL")
                item.uploadPoster(url=local_source)
        else:
            logging.info(f"DRY_RUN - NO ACTION TAKEN")
    
    sleep_for_a_while()
            

def get_art_source(bar, item, local_file, poster_path, dl_URL):
    art_source = None

    if LOCAL_RESET_ARCHIVE:
        bar_and_log(bar, f"Checking local archive for {item.title}-{item.ratingKey}")

        if local_file is None or not os.path.exists(local_file):
            ext = pathlib.Path(poster_path).suffix
            local_file = os.path.join(tgt_dir, f"{item.ratingKey}.{ext}")
            if item.TYPE == 'season':
                local_file = os.path.join(tgt_dir,f"{item.ratingKey}-S{item.seasonNumber}{ext}",)
            if item.TYPE == 'episode':
                local_file = os.path.join(tgt_dir,f"{item.ratingKey}-S{item.seasonNumber}E{item.episodeNumber}.{ext}",)

        if not os.path.exists(local_file):
            bar_and_log(bar, f"-> no local_file, downloading: {dl_URL}")
            if not DRY_RUN:
                r = requests.get(dl_URL, allow_redirects=True)
                # should be checking status
                open(f"{local_file}", "wb").write(r.content)
            else:
                logging.info(f"DRY_RUN - NO ACTION TAKEN")

        art_source = local_file
    else:
        art_source = dl_URL

    return art_source

def track_completion(id_array, status_file, item_id):
    id_array.append(f"{item_id}")

    if not DRY_RUN:
        with open(status_file, "a", encoding="utf-8") as sf:
            sf.write(f"{item_id}{os.linesep}")
    
for lib in LIB_ARRAY:
    id_array = []
    the_lib = plex.library.section(lib)
    status_file_name = the_lib.uuid + ".txt"
    status_file = Path(status_file_name)

    if status_file.is_file():
        if FLUSH_STATUS_AT_START and not DRY_RUN:
            status_file.unlink()
        else:
            with open(f"{status_file_name}") as fp:
                for line in fp:
                    id_array.append(line.strip())

    for lbl in LBL_ARRAY:
        if lbl == "xy22y1973":
            print(f"{os.linesep}getting all items from the library [{lib}]...")
            library_items = get_all_from_library(plex, the_lib)
            REMOVE_LABELS = False
        else:
            print(
                f"{os.linesep}getting items from the library [{lib}] with the label [{lbl}]..."
            )
            library_items = the_lib.search(label=lbl)
        item_total = len(library_items)
        print_and_log(f"{item_total} item(s) retrieved...")
        item_count = 1
        with alive_bar(item_total, dual_line=True, title="Poster Reset - TMDB") as bar:
            for library_item in library_items:
                item_count = item_count + 1
                item_key = library_item.ratingKey
                item_title = library_item.title
                imdbid, tmdb_id, tvdb_id = get_ids(library_item.guids, TMDB_KEY)
                logging.info(f"{item_title}: ratingKey: {item_key} imdbid: {imdbid} tmdb_id: {tmdb_id} tvdb_id: {tvdb_id}")
                try:
                    bar_and_log(bar, f"-> starting: {item_title}")
                    poster_path = None
                    local_file = None
                    tmdb_item = get_tmdb_item(tmdb_id, tvdb_id)

                    tgt_dir = show_dir if library_item.TYPE == "show" else movie_dir

                    if LOCAL_RESET_ARCHIVE:
                        local_file = localFilePath(tgt_dir, item_key)
                        poster_path = local_file
    
                    if local_file is None:
                        poster_path = get_base_tmdb_image(item_title, tmdb_id)

                    if poster_path is not None:
                        seriesPosterURL = f"{base_url}{size_str}{poster_path}"
                        logging.info(f"top-level poster URL: {seriesPosterURL}")

                        if id_array.count(f"{item_key}-top") == 0:
                            logging.info(f"{item_title}: haven't reset this yet")
                            
                            if poster_path is not None:
                                dl_URL = seriesPosterURL

                                bar_and_log(bar, f"-> checking if Plex knows about this image: {seriesPosterURL}")
                                plex_poster = plex_knows_this_image(library_item, 'tmdb', seriesPosterURL)
                                if plex_poster is not None:
                                    dl_URL = plex_poster.key
                                    bar_and_log(bar, f"-> poster will come from plex: {dl_URL}")

                                art_source = get_art_source(bar, library_item, local_file, poster_path, dl_URL)

                                set_or_upload_image(bar, library_item, plex_poster, art_source)

                                track_completion(id_array, status_file, f"{item_key}-top")

                        else:
                            bar_and_log(bar, f"Skipping {item_title}-{item_key}: already reset")

                        if library_item.TYPE == "show" and tmdb_item is not None:

                            if RESET_SEASONS:
                                bar_and_log(bar, f"Resetting seasons for {item_title}-{item_key}")
                                # get seasons
                                plex_seasons = library_item.seasons()
                                sleep_for_a_while()
                                tmdb_seasons = tmdb_item.seasons

                                # loop over all:
                                for plex_season in plex_seasons:
                                    plex_s_id = plex_season.seasonNumber
                                    plex_s_key = plex_season.ratingKey
                                    plex_s_found = False

                                    bar_and_log(bar, f"Processing {item_title}-{item_key} Season {plex_s_id}")

                                    for tmdb_season in tmdb_seasons:
                                        tmdb_season.reload()

                                        if tmdb_season.season_number == plex_s_id and not plex_s_found:
                                            bar_and_log(bar, f"{item_title}-{item_key} Season {plex_s_id} found matching season at TMDB")
                                            plex_s_found = True

                                            if id_array.count(f"{plex_s_key}") == 0:
                                                poster_path = tmdb_season.poster_path
                                                poster_url = None

                                                if poster_path is None and RESET_SEASONS_WITH_SERIES:
                                                    posterURL = seriesPosterURL
                                                    poster_path = posterURL.rsplit("/", 1)[-1]
                                                
                                                if poster_path is not None:
                                                    if poster_url is None:
                                                        poster_url = (
                                                            f"{base_url}{size_str}{poster_path}"
                                                        )
                                                    local_file = localFilePath(
                                                        tgt_dir, f"{item_key}-S{plex_s_id}"
                                                    )
                                                    logging.info(f"season poster_url: {poster_url}")

                                                    dl_URL = poster_url
                                                    
                                                    bar_and_log(bar, f"-> checking if Plex knows about this image: {poster_url}")
                                                    plex_poster = plex_knows_this_image(plex_season, 'tmdb', poster_url)

                                                    if plex_poster is not None:
                                                        dl_URL = plex_poster.key
                                                        bar_and_log(bar, f"-> poster will come from plex: {dl_URL}")

                                                    art_source = get_art_source(bar, plex_season, local_file, poster_path, dl_URL)

                                                    set_or_upload_image(bar, plex_season, plex_poster, art_source)
                                                    
                                                    track_completion(id_array, status_file, f"{plex_s_key}")

                                                else:
                                                    bar_and_log(bar, f"NO SEASON POSTER ON TMDB and RESET_SEASONS_WITH_SERIES turned off; PLEX ART WILL NOT BE TOUCHED")

                                            else:
                                                bar_and_log(bar, f"Skipping {item_title}-{item_key} Season {plex_s_id}-{plex_s_key}: already reset")

                                            if REMOVE_LABELS:
                                                bar_and_log(bar, f"-> removing label {lbl}: Season {plex_s_id}")
                                                plex_season.removeLabel(lbl, True)

                                            if RESET_EPISODES:
                                                # get episodes
                                                bar_and_log(bar, f"getting TMDB episodes for season: {tmdb_season.season_number}")
                                                tmdb_episodes = tmdb_season.episodes
                                                bar_and_log(bar, f"getting Plex episodes for season: {plex_s_id}")
                                                episodes = plex_season.episodes()
                                                sleep_for_a_while()

                                                bar_and_log(bar, f"Looping over Plex episodes:")
                                                for plex_ep in episodes:
                                                    plex_e_id = plex_ep.episodeNumber
                                                    plex_e_key = plex_ep.ratingKey
                                                    plex_e_found = False
                                                    if id_array.count(f"{plex_e_key}") == 0:
                                                        bar_and_log(bar, f"Looping over TMDB episodes:")
                                                        for tmdb_ep in tmdb_episodes:
                                                            tmdb_s_id = None
                                                            tmdb_e_id = None
                                                            try:
                                                                tmdb_s_id = tmdb_ep.season_number
                                                                tmdb_e_id = tmdb_ep.episode_number
                                                            except Exception as ex:
                                                                bar_and_log(bar, f"-> EXCEPTION getting TMDB season or episode ID: {ex}")

                                                            if tmdb_s_id is not None and tmdb_e_id is not None:
                                                                if not plex_e_found and tmdb_s_id == plex_s_id and tmdb_e_id == plex_e_id:
                                                                    bar_and_log(bar, f"Found episode S{plex_s_id} E{plex_e_id}")
                                                                    #  that's the one
                                                                    plex_e_found = True
                                                                    poster_path = tmdb_ep.still_path

                                                                    if poster_path is not None:
                                                                        bar_and_log(bar, f"-> poster_path: {poster_path}")
                                                                        posterURL = f"{base_url}{size_str}{poster_path}"
                                                                        local_file = localFilePath(tgt_dir,f"{item_key}-S{plex_s_id}E{plex_e_id}",)

                                                                        dl_URL = posterURL

                                                                        bar_and_log(bar, f"-> checking if Plex knows about this image: {posterURL}")
                                                                        plex_poster = plex_knows_this_image(plex_ep, 'tmdb', posterURL)

                                                                        art_source = get_art_source(bar, plex_ep, local_file, poster_path, dl_URL)

                                                                        set_or_upload_image(bar, plex_ep, plex_poster, art_source)

                                                                        track_completion(id_array, status_file, f"{plex_e_key}")

                                                                        if REMOVE_LABELS:
                                                                            bar_and_log(bar, f"-> removing label {lbl}: Season {plex_s_id}")
                                                                            plex_ep.removeLabel(lbl, True)

                                                                    else:
                                                                        bar_and_log(bar, f"NO EPISODE POSTER ON TMDB; PLEX ART WILL NOT BE TOUCHED")


                                                            else:
                                                                bar_and_log(bar, f"-> Couldn't get some episode details")
                                                    
                                                        if not plex_e_found:
                                                            bar_and_log(bar, f"NO TMDB match found for Plex episode {plex_s_id}-{plex_e_id}")

                                                    else:
                                                        bar_and_log(bar, f"Skipping {item_title}-{item_key} Season {plex_s_id}-{plex_s_key} Episode {plex_e_id}-{plex_e_key}: already reset")

                                    if not plex_s_found:
                                        bar_and_log(bar, f"NO TMDB match found for Plex season {plex_s_id}")

                        if REMOVE_LABELS:
                            bar_and_log(bar, f"-> removing label {lbl}: {item_title}")
                            library_item.removeLabel(lbl, True)
                    else:
                        bar_and_log(bar, f"NO TMDB poster available for {item_title}")

                except Exception as ex:
                    print_and_log(f'Exception processing "{item_title}": {ex}')
                    # there's a 500 in the season poster upload

                bar()

                logging.info(f'COMPLETE processing on {item_title}')

    # delete the status file
    if not RETAIN_RESET_STATUS_FILE and not DRY_RUN:
        if status_file.is_file():
            os.remove(status_file)

end = timer()
elapsed = end - start
print_and_log(f"{os.linesep}{os.linesep}processing complete in {elapsed:.2f} seconds.")
