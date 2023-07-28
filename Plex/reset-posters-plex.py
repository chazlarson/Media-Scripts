from plexapi.exceptions import Unauthorized
import logging
from alive_progress import alive_bar
from plexapi.server import PlexServer
from plexapi.exceptions import Unauthorized
import os
from dotenv import load_dotenv, set_key, unset_key

from timeit import default_timer as timer
import time
from helpers import booler, get_all_from_library, get_plex, load_and_upgrade_env
from pathlib import Path
import random

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

def bar_and_log(the_bar, msg):
    logging.info(msg)
    the_bar.text = msg

def print_and_log(msg):
    logging.info(msg)
    print(msg)

print_and_log(f"Starting {SCRIPT_NAME}")

status = load_and_upgrade_env(env_file_path)

LIBRARY_NAME = os.getenv("LIBRARY_NAME")
LIBRARY_NAMES = os.getenv("LIBRARY_NAMES")
TARGET_LABELS = os.getenv("TARGET_LABELS")
TRACK_RESET_STATUS = os.getenv("TRACK_RESET_STATUS")
RETAIN_RESET_STATUS_FILE = os.getenv("RETAIN_RESET_STATUS_FILE")
DRY_RUN = booler(os.getenv("DRY_RUN"))
FLUSH_STATUS_AT_START = booler(os.getenv("FLUSH_STATUS_AT_START"))
RESET_SEASONS_WITH_SERIES = booler(os.getenv("RESET_SEASONS_WITH_SERIES"))

REMOVE_LABELS = booler(os.getenv("REMOVE_LABELS"))
RESET_SEASONS = booler(os.getenv("RESET_SEASONS"))
RESET_EPISODES = booler(os.getenv("RESET_EPISODES"))

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

plex = get_plex()
print_and_log("connection success")

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

def get_log_title(item):
    if item.type == 'season':
        return f"{item.parentTitle}-{item.seasonNumber}-{item.title}"
    elif item.type == 'episode':
        return f"{item.grandparentTitle}-{item.seasonEpisode}-{item.title}"
    else:
        return f"{item.title}"

def pick_poster(poster_list, fallback):
    the_poster = None
    if len(posters) > 0:
        bar_and_log(bar, f"-> picking the first poster in the list")
        the_poster = posters[0]
    else:
        if RESET_SEASONS_WITH_SERIES:
            the_poster = fallback
            bar_and_log(bar, f"-> empty list, using fallback")

    return the_poster

def apply_poster(item, item_poster):
    if item_poster is not None:
        bar_and_log(bar, f"-> setting {item.type} poster : {get_log_title(item)} to {item_poster.thumb}")
        if not DRY_RUN:
            item.setPoster(item_poster)
    else:
        bar_and_log(bar, f"-> No poster; no action being taken")


def track_completion(id_array, status_file, item_id):
    id_array.append(f"{item_id}")

    if not DRY_RUN:
        with open(status_file, "a", encoding="utf-8") as sf:
            sf.write(f"{item_id}{os.linesep}")

for lib in LIB_ARRAY:
    id_array = []
    the_lib = plex.library.section(lib)
    the_type = the_lib.type
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
            print_and_log(f"getting all items from the {the_type} library [{lib}]...")
            items = get_all_from_library(plex, the_lib)
            REMOVE_LABELS = False
        else:
            print_and_log(
                f"getting items from the {the_type} library [{lib}] with the label [{lbl}]..."
            )
            items = the_lib.search(label=lbl)
        item_total = len(items)
        print_and_log(f"{item_total} item(s) retrieved...")
        item_count = 1
        with alive_bar(item_total, dual_line=True, title="Poster Reset - Plex") as bar:
            for item in items:
                item_count = item_count + 1
                if id_array.count(f"{item.ratingKey}") == 0:
                    item_title = get_log_title(item)
                    try:
                        bar_and_log(bar, f"-> starting: {item_title}")
                        pp = None
                        local_file = None

                        bar_and_log(bar, f"-> getting posters: {item_title}")
                        posters = item.posters()
                        bar_and_log(bar, f"-> Plex has {len(posters)} posters for: {item_title}")

                        showPoster = pick_poster(posters, None)
                        
                        apply_poster(item, showPoster)

                        # Wait between items in case hammering the Plex server turns out badly.
                        sleep_for_a_while()

                        if REMOVE_LABELS:
                            bar_and_log(bar, f"-> removing label {lbl}: {item_title}")
                            item.removeLabel(lbl, True)

                        track_completion(id_array, status_file, f"{item.ratingKey}")
                        
                        if item.TYPE == "show":
                            if RESET_SEASONS:
                                # get seasons
                                seasons = item.seasons()
                                bar_and_log(bar, f"-> Plex has {len(seasons)} seasons for: {item_title}")
                                # loop over all:
                                for s in seasons:
                                    if id_array.count(f"{s.ratingKey}") == 0:
                                        item_title = get_log_title(s)
                                        # reset artwork
                                        bar_and_log(bar, 
                                            f"-> getting season posters: {item_title}"
                                        )
                                        posters = s.posters()
                                        bar_and_log(bar, f"-> Plex has {len(posters)} posters for: {item_title}")

                                        seasonPoster = pick_poster(posters, showPoster)
                                        
                                        apply_poster(s, seasonPoster)

                                        # Wait between items in case hammering the Plex server turns out badly.
                                        sleep_for_a_while()

                                        track_completion(id_array, status_file, f"{s.ratingKey}")

                                    if RESET_EPISODES:
                                        # get episodes
                                        episodes = s.episodes()
                                        # loop over all
                                        for e in episodes:
                                            if id_array.count(f"{e.ratingKey}") == 0:
                                                item_title = get_log_title(e)
                                                # reset artwork
                                                bar_and_log(bar, f"-> getting episode posters: {item_title}")
                                                posters = e.posters()

                                                bar_and_log(bar, f"-> Plex has {len(posters)} posters for: {item_title}")

                                                episodePoster = pick_poster(posters, None)

                                                apply_poster(e, episodePoster)

                                                # Wait between items in case hammering the Plex server turns out badly.
                                                sleep_for_a_while()

                                                track_completion(id_array, status_file, f"{e.ratingKey}")

                    except Exception as ex:
                        print_and_log(f'Exception processing "{item.title}": {ex}')

                    bar()

                    # Wait between items in case hammering the Plex server turns out badly.
                    sleep_for_a_while()

    # delete the status file
    if not RETAIN_RESET_STATUS_FILE and not DRY_RUN:
        if status_file.is_file():
            os.remove(status_file)

end = timer()
elapsed = end - start
print_and_log(f"{os.linesep}{os.linesep}processed {item_count - 1} items in {elapsed} seconds.")
