""" Reset the posters for all items in a Plex library """
#!/usr/bin/env python
import os
import sys
import time
import random
from pathlib import Path
from datetime import datetime
from timeit import default_timer as timer
from logs import setup_logger, plogger, blogger

from alive_progress import alive_bar
from helpers import booler, get_all_from_library, get_plex, load_and_upgrade_env, get_overlay_status

start = timer()

# current dateTime
now = datetime.now()

# convert to string
RUNTIME_STR = now.strftime("%Y-%m-%d %H:%M:%S")

SCRIPT_NAME = Path(__file__).stem

# DONE 0.1.1 added a couple booler
# DONE 0.1.2 Require a meaningful value for TARGET_LABELS
# DONE 0.1.3 Batch remove labels

VERSION = "0.1.3"

env_file_path = Path(".env")

ACTIVITY_LOG = f"{SCRIPT_NAME}.log"
setup_logger('activity_log', ACTIVITY_LOG)

plogger(f"Starting {SCRIPT_NAME} {VERSION} at {RUNTIME_STR}", 'info', 'a')

if load_and_upgrade_env(env_file_path) < 0:
    sys.exit()

LIBRARY_NAME = os.getenv("LIBRARY_NAME")
LIBRARY_NAMES = os.getenv("LIBRARY_NAMES")
TARGET_LABELS = os.getenv("TARGET_LABELS")

if TARGET_LABELS == 'this label, that label':
    print("TARGET_LABELS in the .env file must be empty or have a meaningful value.", 'info', 'a')
    sys.exit()

TRACK_RESET_STATUS = booler(os.getenv("TRACK_RESET_STATUS"))
RETAIN_RESET_STATUS_FILE = booler(os.getenv("RETAIN_RESET_STATUS_FILE"))
DRY_RUN = booler(os.getenv("DRY_RUN"))
FLUSH_STATUS_AT_START = booler(os.getenv("FLUSH_STATUS_AT_START"))
RESET_SEASONS_WITH_SERIES = booler(os.getenv("RESET_SEASONS_WITH_SERIES"))
OVERRIDE_OVERLAY_STATUS = booler(os.getenv("OVERRIDE_OVERLAY_STATUS"))

REMOVE_LABELS = booler(os.getenv("REMOVE_LABELS"))
RESET_SEASONS = booler(os.getenv("RESET_SEASONS"))
RESET_EPISODES = booler(os.getenv("RESET_EPISODES"))

DELAY = 0
try:
    DELAY = int(os.getenv("DELAY"))
except: # pylint: disable=bare-except
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
plogger("connection success", 'info', 'a')

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

def get_log_title(tgt_item):
    """ Get the title for logging """
    if tgt_item.type == 'season':
        return f"{tgt_item.parentTitle}-{tgt_item.seasonNumber}-{tgt_item.title}"

    if tgt_item.type == 'episode':
        return f"{tgt_item.grandparentTitle}-{tgt_item.seasonEpisode}-{tgt_item.title}"

    return f"{tgt_item.title}"

def pick_poster(poster_list, fallback, the_bar):
    """ Pick a poster from the list """
    the_poster = None
    if len(posters) > 0:
        blogger("-> picking the first poster in the list", 'info', 'a', the_bar)
        the_poster = poster_list[0]
    else:
        if RESET_SEASONS_WITH_SERIES:
            the_poster = fallback
            blogger("-> empty list, using fallback", 'info', 'a', the_bar)

    return the_poster

def apply_poster(tgt_item, item_poster):
    """ Apply the poster to the item """
    if item_poster is not None:
        blogger(f"-> setting {tgt_item.type} poster : {get_log_title(tgt_item)} to {item_poster.thumb}", 'info', 'a', bar)
        if not DRY_RUN:
            tgt_item.setPoster(item_poster)
    else:
        blogger("-> No poster; no action being taken", 'info', 'a', bar)


def track_completion(the_id_array, the_status_file, item_id):
    """ Track the completion of an item """
    the_id_array.append(f"{item_id}")

    if not DRY_RUN:
        with open(the_status_file, "a", encoding="utf-8") as sf:
            sf.write(f"{item_id}{os.linesep}")

ITEM_COUNT = 1

for lib in LIB_ARRAY:
    id_array = []
    the_lib = plex.library.section(lib)
    the_type = the_lib.type
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
            plogger(f"getting all items from the {the_type} library [{lib}]...", 'info', 'a')
            ITEM_COUNT, items = get_all_from_library(the_lib)
            REMOVE_LABELS = False
        else:
            plogger(
                f"getting items from the {the_type} library [{lib}] with the label [{lbl}]...", 'info', 'a'
            )
            items = the_lib.search(label=lbl)
        item_total = len(items)
        plogger(f"{item_total} item(s) retrieved...", 'info', 'a')
        ITEM_COUNT = 1
        with alive_bar(item_total, dual_line=True, title="Poster Reset - Plex") as bar:
            for item in items:
                ITEM_COUNT = ITEM_COUNT + 1
                if id_array.count(f"{item.ratingKey}") == 0:
                    ITEM_TITLE = get_log_title(item)
                    try:
                        blogger(f"-> starting: {ITEM_TITLE}", 'info', 'a', bar)
                        PP = None
                        LOCAL_FILE = None

                        blogger(f"-> getting posters: {ITEM_TITLE}", 'info', 'a', bar)
                        posters = item.posters()
                        blogger(f"-> Plex has {len(posters)} posters for: {ITEM_TITLE}", 'info', 'a', bar)

                        showPoster = pick_poster(posters, None, bar)

                        apply_poster(item, showPoster)

                        # Wait between items in case hammering the Plex server turns out badly.
                        sleep_for_a_while()

                        if REMOVE_LABELS:
                            blogger(f"-> removing label {lbl}: {ITEM_TITLE}", 'info', 'a', bar)
                            item.removeLabel(lbl, True)

                        track_completion(id_array, status_file, f"{item.ratingKey}")

                        if item.TYPE == "show":
                            if RESET_SEASONS:
                                # get seasons
                                seasons = item.seasons()
                                blogger(f"-> Plex has {len(seasons)} seasons for: {ITEM_TITLE}", 'info', 'a', bar)
                                # loop over all:
                                for s in seasons:
                                    if id_array.count(f"{s.ratingKey}") == 0:
                                        ITEM_TITLE = get_log_title(s)
                                        # reset artwork
                                        blogger(f"-> getting season posters: {ITEM_TITLE}", 'info', 'a', bar)
                                        posters = s.posters()
                                        blogger(f"-> Plex has {len(posters)} posters for: {ITEM_TITLE}", 'info', 'a', bar)

                                        seasonPoster = pick_poster(posters, showPoster, bar)

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
                                                ITEM_TITLE = get_log_title(e)
                                                # reset artwork
                                                blogger(f"-> getting episode posters: {ITEM_TITLE}", 'info', 'a', bar)
                                                posters = e.posters()

                                                blogger(f"-> Plex has {len(posters)} posters for: {ITEM_TITLE}", 'info', 'a', bar)

                                                episodePoster = pick_poster(posters, None, bar)

                                                apply_poster(e, episodePoster)

                                                # Wait between items in case hammering the Plex server turns out badly.
                                                sleep_for_a_while()

                                                track_completion(id_array, status_file, f"{e.ratingKey}")

                    except Exception as ex: # pylint: disable=broad-exception-caught
                        plogger(f'Exception processing "{item.title}": {ex}', 'info', 'a')

                    bar() # pylint: disable=not-callable

                    # Wait between items in case hammering the Plex server turns out badly.
                    sleep_for_a_while()

        if REMOVE_LABELS:
            the_lib.batchMultiEdits(items)
            the_lib.removeLabel(lbl)
            the_lib.saveMultiEdits()

    # delete the status file
    if not RETAIN_RESET_STATUS_FILE and not DRY_RUN:
        if status_file.is_file():
            os.remove(status_file)

end = timer()
elapsed = end - start
plogger(f"{os.linesep}{os.linesep}processed {ITEM_COUNT - 1} items in {elapsed:.2f} seconds.", 'info', 'a')
