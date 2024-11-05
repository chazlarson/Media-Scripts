""" Reset posters for all items in a library to the TMDB poster """
#!/usr/bin/env python

import os
import sys
import pathlib
from pathlib import Path
import platform
from timeit import default_timer as timer
import time
import random
from datetime import datetime
import validators
import requests
from tmdbapis import TMDbAPIs
from alive_progress import alive_bar
from logs import setup_logger, plogger, blogger, logger
from helpers import booler, get_all_from_library, get_ids, get_plex, load_and_upgrade_env, get_overlay_status

# import tvdb_v4_official

start = timer()

# current dateTime
now = datetime.now()

# convert to string
RUNTIME_STR = now.strftime("%Y-%m-%d %H:%M:%S")

SCRIPT_NAME = Path(__file__).stem

# DONE 0.1.2 Batch remove labels

VERSION = "0.1.2"

env_file_path = Path(".env")

ACTIVITY_LOG = f"{SCRIPT_NAME}.log"
setup_logger('activity_log', ACTIVITY_LOG)

plogger(f"Starting {SCRIPT_NAME} {VERSION} at {RUNTIME_STR}", 'info', 'a')

if load_and_upgrade_env(env_file_path) < 0:
    sys.exit()

LIBRARY_NAME = os.getenv("LIBRARY_NAME")
LIBRARY_NAMES = os.getenv("LIBRARY_NAMES")
tmdb_key = os.getenv("TMDB_KEY")
TVDB_KEY = os.getenv("TVDB_KEY")
TARGET_LABELS = os.getenv("TARGET_LABELS")

if TARGET_LABELS == 'this label, that label':
    print("TARGET_LABELS in the .env file must be empty or have a meaningful value.")
    sys.exit()

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
OVERRIDE_OVERLAY_STATUS = booler(os.getenv("OVERRIDE_OVERLAY_STATUS"))

DELAY = 0
try:
    DELAY = int(os.getenv("DELAY"))
except: # pylint: disable=bare-except
    DELAY = 0

if TARGET_LABELS:
    LBL_ARRAY = TARGET_LABELS.split(",")
else:
    print("defaulting label array")
    LBL_ARRAY = ["xy22y1973"]

if LIBRARY_NAMES:
    LIB_ARRAY = LIBRARY_NAMES.split(",")
else:
    LIB_ARRAY = [LIBRARY_NAME]

IS_WINDOWS = platform.system() == "Windows"

# Commented out until this doesn't throw a 400
# tvdb = tvdb_v4_official.TVDB(TVDB_KEY)

tmdb = TMDbAPIs(tmdb_key, language="en")

local_dir = os.path.join(os.getcwd(), "posters")

os.makedirs(local_dir, exist_ok=True)

show_dir = os.path.join(os.getcwd(), "shows")
movie_dir = os.path.join(os.getcwd(), "movies")

os.makedirs(show_dir, exist_ok=True)
os.makedirs(movie_dir, exist_ok=True)

def local_file_path(target_dir, rating_key):
    """ Return the local file path for the given rating key """
    for ext in ["jpg", "png"]:
        local_file = os.path.join(target_dir, f"{rating_key}.{ext}")
        if os.path.exists(local_file):
            return local_file
    return None


print("tmdb config...")

base_url = tmdb.configuration().secure_base_image_url
SIZE_STR = "original"

plex = get_plex()

logger(("connection success"), 'info', 'a')

if LIBRARY_NAMES == 'ALL_LIBRARIES':
    LIB_ARRAY = []
    all_libs = plex.library.sections()
    for lib in all_libs:
        if lib.type in ('movie', 'show'):
            LIB_ARRAY.append(lib.title.strip())

def sleep_for_a_while():
    """ Sleep for a random amount of time """
    sleeptime = DELAY
    if DELAY == 99:
        sleeptime = random.uniform(0, 1)

    time.sleep(sleeptime)

def plex_knows_this_image(item, source, dl_url):
    """ Check if Plex knows about this image """
    logger((f"Retrieving posters for Plex {item.type}: {item.title} "), 'info', 'a')
    # item.reload()
    attempts = 0
    while attempts < 5:
        try:
            list_of_posters = item.posters()
            sleep_for_a_while()
            logger((f"Checking {len(list_of_posters)} posters"), 'info', 'a')
            for poster in list_of_posters:
                if poster.provider == source:
                    if poster.key == dl_url:
                        logger((f"This is one of Plex' posters: {dl_url}"), 'info', 'a')
                        return poster
            attempts = 6
        except Exception as ex: # pylint: disable=broad-exception-caught
            logger((f'Exception processing "{item}": {ex}'), 'info', 'a')
            attempts += 1

    return None

def get_tmdb_item(p_tmdb_id, p_tvdb_id):
    """ Get the TMDB item """
    rv_tmdb_item = None

    if p_tmdb_id is None and p_tvdb_id is None:
        return rv_tmdb_item

    if library_item.TYPE == "show":
        if p_tmdb_id is not None:
            logger((f"{item_title}: tmdb_id: {p_tmdb_id} - getting tv_show"), 'info', 'a')
            rv_tmdb_item = tmdb.tv_show(p_tmdb_id)
            logger((f"{item_title}: tmdb_id: {p_tmdb_id} - FOUND {rv_tmdb_item.title}"), 'info', 'a')
        else:
            logger((f"{item_title}: no tmdb_id, trying tvdb_id"), 'info', 'a')
            if p_tvdb_id is not None:
                logger((f"{item_title}: tvdb_id: {p_tvdb_id} - SEARCHING FOR tv_show"), 'info', 'a')
                tmdb_search = (
                    tmdb.find_by_id(tvdb_id=p_tvdb_id)
                )
                if len(tmdb_search.tv_results) > 0:
                    rv_tmdb_item = tmdb_search.tv_results[0]
                    logger((f"{item_title}: tvdb_id: {p_tvdb_id} - FOUND {rv_tmdb_item.title}"), 'info', 'a')
            else:
                logger((f"{item_title}: no tvdb_id specified"), 'info', 'a')


    else:
        if p_tmdb_id is not None:
            logger((f"{item_title}: tmdb_id: {p_tmdb_id} - getting movie"), 'info', 'a')
            rv_tmdb_item = tmdb.movie(p_tmdb_id)
            logger((f"{item_title}: tmdb_id: {p_tmdb_id} - FOUND {rv_tmdb_item.title}"), 'info', 'a')

    return rv_tmdb_item

def get_base_tmdb_image(p_item_title, p_tmdb_id):
    """ Get the base TMDB image """
    tmdb_base = None

    logger((f"{p_item_title}: tmdb_id: {p_tmdb_id} - NO LOCAL FILE"), 'info', 'a')
    try:
        logger((f"{p_item_title}: tmdb_id: {p_tmdb_id} - RELOADING ITEM"), 'info', 'a')
        tmdb_item.reload()
        tmdb_base = tmdb_item.poster_path
    except Exception as ex: # pylint: disable=broad-exception-caught
        logger((f"{p_item_title}: tmdb_id: {p_tmdb_id} - EXCEPTION {ex}"), 'info', 'a')
        tmdb_base = None

    return tmdb_base

def set_or_upload_image(p_bar, item, p_plex_poster, local_source):
    """ Set or upload the image """
    if p_plex_poster is not None:
        blogger(f"-> SETTING poster for {item.type} {item.title} to {p_plex_poster.key}", 'info', 'a', p_bar)
        item.setPoster(p_plex_poster)
    else:
        blogger(f"-> UPLOADING poster for {item.type} {item.title} from {local_source}", 'info', 'a', p_bar)
        if not DRY_RUN:
            if not validators.url(local_source):
                logger((f"{local_source}: appears to be a file"), 'info', 'a')
                item.uploadPoster(filepath=local_source)
            else:
                logger((f"{local_source}: appears to be a URL"), 'info', 'a')
                item.uploadPoster(url=local_source)
        else:
            logger(("DRY_RUN - NO ACTION TAKEN"), 'info', 'a')

    sleep_for_a_while()


def get_art_source(p_bar, item, local_file, poster_path, dl_url):
    """ Get the art source """
    rv_art_source = None

    if LOCAL_RESET_ARCHIVE:
        blogger(f"Checking local archive for {item.title}-{item.ratingKey}", 'info', 'a', p_bar)

        if local_file is None or not os.path.exists(local_file):
            ext = pathlib.Path(poster_path).suffix
            local_file = os.path.join(tgt_dir, f"{item.ratingKey}.{ext}")
            if item.TYPE == 'season':
                local_file = os.path.join(tgt_dir,f"{item.ratingKey}-S{item.seasonNumber}{ext}",)
            if item.TYPE == 'episode':
                local_file = os.path.join(tgt_dir,f"{item.ratingKey}-S{item.seasonNumber}E{item.episodeNumber}.{ext}",)

        if not os.path.exists(local_file):
            blogger(f"-> no local_file, downloading: {dl_url}", 'info', 'a', p_bar)
            if not DRY_RUN:
                r = requests.get(dl_url, allow_redirects=True, timeout=30)
                # should be checking status
                with open(f"{local_file}", "wb") as lf: # pylint: disable=unspecified-encoding
                    lf.write(r.content)
            else:
                logger(("DRY_RUN - NO ACTION TAKEN"), 'info', 'a')

        rv_art_source = local_file
    else:
        rv_art_source = dl_url

    return rv_art_source

def track_completion(the_id_array, the_status_file, item_id):
    """ Track the completion """
    the_id_array.append(f"{item_id}")

    if not DRY_RUN:
        with open(the_status_file, "a", encoding="utf-8") as sf:
            sf.write(f"{item_id}{os.linesep}")

ITEM_COUNT = 1

for lib in LIB_ARRAY:
    id_array = []
    the_lib = plex.library.section(lib)
    status_file_name = the_lib.uuid + ".txt"
    status_file = Path(status_file_name)

    if get_overlay_status(the_lib) and not OVERRIDE_OVERLAY_STATUS:
        print("==================== ATTENTION ====================")
        print(f"Library: {lib}")
        print("This library appears to have Kometa overlays applied.")
        print("The artwork that this script sets will be overwritten")
        print("by Kometa the next time it runs.")
        print("This is probably not what you want.")
        print("You should remove the 'Overlay' label from everything")
        print("in the library before running Kometa again.")
        print("For safety, the script will ignore this library.")
        print("==================== ATTENTION ====================")
        print("To ignore this warning and run this script anyway,")
        print("add 'OVERRIDE_OVERLAY_STATUS=1' to .env")
        continue

    if status_file.is_file():
        if FLUSH_STATUS_AT_START and not DRY_RUN:
            status_file.unlink()
        else:
            with open(f"{status_file_name}") as fp: # pylint: disable=unspecified-encoding
                for line in fp:
                    id_array.append(line.strip())

    for lbl in LBL_ARRAY:
        if lbl == "xy22y1973":
            print(f"{os.linesep}getting all items from the library [{lib}]...")
            library_items_counts, library_items = get_all_from_library(the_lib)
            REMOVE_LABELS = False
        else:
            print(
                f"{os.linesep}getting items from the library [{lib}] with the label [{lbl}]..."
            )
            library_items = the_lib.search(label=lbl)
        item_total = len(library_items)
        plogger(f"{item_total} item(s) retrieved...", 'info', 'a')
        ITEM_COUNT = 1
        with alive_bar(item_total, dual_line=True, title="Poster Reset - TMDB") as bar:
            for library_item in library_items:
                ITEM_COUNT = ITEM_COUNT + 1
                item_key = library_item.ratingKey
                item_title = library_item.title
                imdbid, tmdb_id, tvdb_id = get_ids(library_item.guids)
                logger((f"{item_title}: ratingKey: {item_key} imdbid: {imdbid} tmdb_id: {tmdb_id} tvdb_id: {tvdb_id}"), 'info', 'a')
                try:
                    blogger(f"-> starting: {item_title}", 'info', 'a', bar)
                    POSTER_PATH = None
                    LOCAL_FILE = None
                    tmdb_item = get_tmdb_item(tmdb_id, tvdb_id)

                    tgt_dir = show_dir if library_item.TYPE == "show" else movie_dir

                    if LOCAL_RESET_ARCHIVE:
                        LOCAL_FILE = local_file_path(tgt_dir, item_key)
                        POSTER_PATH = LOCAL_FILE

                    if LOCAL_FILE is None:
                        POSTER_PATH = get_base_tmdb_image(item_title, tmdb_id)

                    if POSTER_PATH is not None:
                        SERIES_POSTER_URL = f"{base_url}{SIZE_STR}{POSTER_PATH}"
                        logger((f"top-level poster URL: {SERIES_POSTER_URL}"), 'info', 'a')

                        if id_array.count(f"{item_key}-top") == 0:
                            logger((f"{item_title}: haven't reset this yet"), 'info', 'a')

                            if POSTER_PATH is not None:
                                DL_URL = SERIES_POSTER_URL

                                blogger(f"-> checking if Plex knows about this image: {SERIES_POSTER_URL}", 'info', 'a', bar)
                                plex_poster = plex_knows_this_image(library_item, 'tmdb', SERIES_POSTER_URL)
                                if plex_poster is not None:
                                    DL_URL = plex_poster.key
                                    blogger(f"-> poster will come from plex: {DL_URL}", 'info', 'a', bar)

                                art_source = get_art_source(bar, library_item, LOCAL_FILE, POSTER_PATH, DL_URL)

                                set_or_upload_image(bar, library_item, plex_poster, art_source)

                                track_completion(id_array, status_file, f"{item_key}-top")

                        else:
                            blogger(f"Skipping {item_title}-{item_key}: already reset", 'info', 'a', bar)

                        if library_item.TYPE == "show" and tmdb_item is not None:

                            if RESET_SEASONS:
                                blogger(f"Resetting seasons for {item_title}-{item_key}", 'info', 'a', bar)
                                # get seasons
                                plex_seasons = library_item.seasons()
                                sleep_for_a_while()
                                tmdb_seasons = tmdb_item.seasons

                                # loop over all:
                                for plex_season in plex_seasons:
                                    plex_s_id = plex_season.seasonNumber
                                    plex_s_key = plex_season.ratingKey
                                    PLEX_S_FOUND = False

                                    blogger(f"Processing {item_title}-{item_key} Season {plex_s_id}", 'info', 'a', bar)

                                    for tmdb_season in tmdb_seasons:
                                        tmdb_season.reload()

                                        if tmdb_season.season_number == plex_s_id and not PLEX_S_FOUND:
                                            blogger(f"{item_title}-{item_key} Season {plex_s_id} found matching season at TMDB", 'info', 'a', bar)
                                            PLEX_S_FOUND = True

                                            if id_array.count(f"{plex_s_key}") == 0:
                                                POSTER_PATH = tmdb_season.poster_path
                                                POSTER_URL = None

                                                if POSTER_PATH is None and RESET_SEASONS_WITH_SERIES:
                                                    POSTER_URL = SERIES_POSTER_URL
                                                    POSTER_PATH = POSTER_URL.rsplit("/", 1)[-1]

                                                if POSTER_PATH is not None:
                                                    if POSTER_URL is None:
                                                        POSTER_URL = (
                                                            f"{base_url}{SIZE_STR}{POSTER_PATH}"
                                                        )
                                                    LOCAL_FILE = local_file_path(
                                                        tgt_dir, f"{item_key}-S{plex_s_id}"
                                                    )
                                                    logger((f"season poster_url: {POSTER_URL}"), 'info', 'a')

                                                    DL_URL = POSTER_URL

                                                    blogger(f"-> checking if Plex knows about this image: {POSTER_URL}", 'info', 'a', bar)
                                                    plex_poster = plex_knows_this_image(plex_season, 'tmdb', POSTER_URL)

                                                    if plex_poster is not None:
                                                        DL_URL = plex_poster.key
                                                        blogger(f"-> poster will come from plex: {DL_URL}", 'info', 'a', bar)

                                                    art_source = get_art_source(bar, plex_season, LOCAL_FILE, POSTER_PATH, DL_URL)

                                                    set_or_upload_image(bar, plex_season, plex_poster, art_source)

                                                    track_completion(id_array, status_file, f"{plex_s_key}")

                                                else:
                                                    blogger("NO SEASON POSTER ON TMDB and RESET_SEASONS_WITH_SERIES turned off; PLEX ART WILL NOT BE TOUCHED", 'info', 'a', bar)

                                            else:
                                                blogger(f"Skipping {item_title}-{item_key} Season {plex_s_id}-{plex_s_key}: already reset", 'info', 'a', bar)

                                            if REMOVE_LABELS:
                                                blogger(f"-> removing label {lbl}: Season {plex_s_id}", 'info', 'a', bar)
                                                plex_season.removeLabel(lbl, True)

                                            if RESET_EPISODES:
                                                # get episodes
                                                blogger(f"getting TMDB episodes for season: {tmdb_season.season_number}", 'info', 'a', bar)
                                                tmdb_episodes = tmdb_season.episodes
                                                blogger(f"getting Plex episodes for season: {plex_s_id}", 'info', 'a', bar)
                                                episodes = plex_season.episodes()
                                                sleep_for_a_while()

                                                blogger("Looping over Plex episodes:", 'info', 'a', bar)
                                                for plex_ep in episodes:
                                                    plex_e_id = plex_ep.episodeNumber
                                                    plex_e_key = plex_ep.ratingKey
                                                    PLEX_E_FOUND = False
                                                    if id_array.count(f"{plex_e_key}") == 0:
                                                        blogger("Looping over TMDB episodes:", 'info', 'a', bar)
                                                        for tmdb_ep in tmdb_episodes:
                                                            TMDB_S_ID = None
                                                            TMDB_E_ID = None
                                                            try:
                                                                TMDB_S_ID = tmdb_ep.season_number
                                                                TMDB_E_ID = tmdb_ep.episode_number
                                                            except Exception as ex: # pylint: disable=broad-exception-caught
                                                                blogger(f"-> EXCEPTION getting TMDB season or episode ID: {ex}", 'info', 'a', bar)

                                                            if TMDB_S_ID is not None and TMDB_E_ID is not None:
                                                                if not PLEX_E_FOUND and TMDB_S_ID == plex_s_id and TMDB_E_ID == plex_e_id:
                                                                    blogger(f"Found episode S{plex_s_id} E{plex_e_id}", 'info', 'a', bar)
                                                                    #  that's the one
                                                                    PLEX_E_FOUND = True
                                                                    POSTER_PATH = tmdb_ep.still_path

                                                                    if POSTER_PATH is not None:
                                                                        blogger(f"-> poster_path: {POSTER_PATH}", 'info', 'a', bar)
                                                                        POSTER_URL = f"{base_url}{SIZE_STR}{POSTER_PATH}"
                                                                        LOCAL_FILE = local_file_path(tgt_dir,f"{item_key}-S{plex_s_id}E{plex_e_id}",)

                                                                        DL_URL = POSTER_URL

                                                                        blogger(f"-> checking if Plex knows about this image: {POSTER_URL}", 'info', 'a', bar)
                                                                        plex_poster = plex_knows_this_image(plex_ep, 'tmdb', POSTER_URL)

                                                                        art_source = get_art_source(bar, plex_ep, LOCAL_FILE, POSTER_PATH, DL_URL)

                                                                        set_or_upload_image(bar, plex_ep, plex_poster, art_source)

                                                                        track_completion(id_array, status_file, f"{plex_e_key}")

                                                                        if REMOVE_LABELS:
                                                                            blogger(f"-> removing label {lbl}: Season {plex_s_id}", 'info', 'a', bar)
                                                                            plex_ep.removeLabel(lbl, True)

                                                                    else:
                                                                        blogger("NO EPISODE POSTER ON TMDB; PLEX ART WILL NOT BE TOUCHED", 'info', 'a', bar)


                                                            else:
                                                                blogger("-> Couldn't get some episode details", 'info', 'a', bar)

                                                        if not PLEX_E_FOUND:
                                                            blogger(f"NO TMDB match found for Plex episode {plex_s_id}-{plex_e_id}", 'info', 'a', bar)

                                                    else:
                                                        blogger(f"Skipping {item_title}-{item_key} Season {plex_s_id}-{plex_s_key} Episode {plex_e_id}-{plex_e_key}: already reset", 'info', 'a', bar) # pylint: disable=line-too-long

                                    if not PLEX_S_FOUND:
                                        blogger(f"NO TMDB match found for Plex season {plex_s_id}", 'info', 'a', bar)

                        if REMOVE_LABELS:
                            blogger(f"-> removing label {lbl}: {item_title}", 'info', 'a', bar)
                            library_item.removeLabel(lbl, True)
                    else:
                        blogger(f"NO TMDB poster available for {item_title}", 'info', 'a', bar)

                except Exception as ex: # pylint: disable=broad-exception-caught
                    plogger(f'Exception processing "{item_title}": {ex}', 'info', 'a')
                    # there's a 500 in the season poster upload

                bar() # pylint: disable=not-callable

                logger((f'COMPLETE processing on {item_title}'), 'info', 'a')

        if REMOVE_LABELS:
            the_lib.batchMultiEdits(library_items)
            the_lib.removeLabel(lbl)
            the_lib.saveMultiEdits()

    # delete the status file
    if not RETAIN_RESET_STATUS_FILE and not DRY_RUN:
        if status_file.is_file():
            os.remove(status_file)

end = timer()
elapsed = end - start
plogger(f"{os.linesep}{os.linesep}processed {ITEM_COUNT - 1} items in {elapsed:.2f} seconds.", 'info', 'a')
