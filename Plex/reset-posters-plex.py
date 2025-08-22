#!/usr/bin/env python

import os
import random
import time
from datetime import datetime
from pathlib import Path
from timeit import default_timer as timer

from alive_progress import alive_bar
from config import Config
from helpers import (get_all_from_library, get_overlay_status, get_plex,
                     get_target_libraries)
from logs import blogger, plogger, setup_logger

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

ACTIVITY_LOG = f"{SCRIPT_NAME}.log"
setup_logger("activity_log", ACTIVITY_LOG)

plogger(f"Starting {SCRIPT_NAME} {VERSION} at {RUNTIME_STR}", "info", "a")

config = Config('../config.yaml')

TARGET_LABELS = config.get('reset_posters.target_labels', '')

if TARGET_LABELS == "this label, that label":
    print(
        "TARGET_LABELS in the config.yaml must be empty or have a meaningful value.",
        "info",
        "a",
    )
    exit()
else:
    if TARGET_LABELS:
        LBL_ARRAY = TARGET_LABELS.split(",")
    else:
        LBL_ARRAY = ["xy22y1973"]

TRACK_RESET_STATUS = config.get_bool('reset_posters.track_reset_status', False)
RETAIN_RESET_STATUS_FILE = config.get_bool('reset_posters.retain_reset_status_file', False)
DRY_RUN = config.get_bool('reset_posters.dry_run', False)
FLUSH_STATUS_AT_START = config.get_bool('reset_posters.flush_status_at_start', False)
RESET_SEASONS_WITH_SERIES = config.get_bool('reset_posters.reset_seasons_with_series', False)
OVERRIDE_OVERLAY_STATUS = config.get_bool('reset_posters.override_overlay_status', False)

REMOVE_LABELS = config.get_bool('reset_posters.remove_labels', False)
RESET_SEASONS = config.get_bool('reset_posters.reset_seasons', False)
RESET_EPISODES = config.get_bool('reset_posters.reset_episodes', False)

DELAY = config.get_int('general.delay', 0)

plex = get_plex()

LIB_ARRAY = get_target_libraries(plex)

def sleep_for_a_while():
    sleeptime = DELAY
    if DELAY == 99:
        sleeptime = random.uniform(0, 1)

    time.sleep(sleeptime)


def get_log_title(item):
    if item.type == "season":
        return f"{item.parentTitle}-{item.seasonNumber}-{item.title}"
    elif item.type == "episode":
        return f"{item.grandparentTitle}-{item.seasonEpisode}-{item.title}"
    else:
        return f"{item.title}"


def pick_poster(poster_list, fallback):
    the_poster = None
    if len(posters) > 0:
        blogger("-> picking the first poster in the list", "info", "a", bar)
        the_poster = posters[0]
    else:
        if RESET_SEASONS_WITH_SERIES:
            the_poster = fallback
            blogger("-> empty list, using fallback", "info", "a", bar)

    return the_poster


def apply_poster(item, item_poster):
    if item_poster is not None:
        blogger(
            f"-> setting {item.type} poster : {get_log_title(item)} to {item_poster.thumb}",
            "info",
            "a",
            bar,
        )
        if not DRY_RUN:
            item.setPoster(item_poster)
    else:
        blogger("-> No poster; no action being taken", "info", "a", bar)


def track_completion(id_array, status_file, item_id):
    id_array.append(f"{item_id}")

    if not DRY_RUN:
        with open(status_file, "a", encoding="utf-8") as sf:
            sf.write(f"{item_id}{os.linesep}")


item_count = 1

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
            with open(f"{status_file_name}") as fp:
                for line in fp:
                    id_array.append(line.strip())

    for lbl in LBL_ARRAY:
        if lbl == "xy22y1973":
            plogger(
                f"getting all items from the {the_type} library [{lib}]...", "info", "a"
            )
            item_count, items = get_all_from_library(the_lib)
            REMOVE_LABELS = False
        else:
            plogger(
                f"getting items from the {the_type} library [{lib}] with the label [{lbl}]...",
                "info",
                "a",
            )
            items = the_lib.search(label=lbl)
        item_total = len(items)
        plogger(f"{item_total} item(s) retrieved...", "info", "a")
        item_count = 1
        with alive_bar(item_total, dual_line=True, title="Poster Reset - Plex") as bar:
            for item in items:
                item_count = item_count + 1
                if id_array.count(f"{item.ratingKey}") == 0:
                    item_title = get_log_title(item)
                    try:
                        blogger(f"-> starting: {item_title}", "info", "a", bar)
                        pp = None
                        local_file = None

                        blogger(f"-> getting posters: {item_title}", "info", "a", bar)
                        posters = item.posters()
                        blogger(
                            f"-> Plex has {len(posters)} posters for: {item_title}",
                            "info",
                            "a",
                            bar,
                        )

                        showPoster = pick_poster(posters, None)

                        apply_poster(item, showPoster)

                        # Wait between items in case hammering the Plex server turns out badly.
                        sleep_for_a_while()

                        if REMOVE_LABELS:
                            blogger(
                                f"-> removing label {lbl}: {item_title}",
                                "info",
                                "a",
                                bar,
                            )
                            item.removeLabel(lbl, True)

                        track_completion(id_array, status_file, f"{item.ratingKey}")

                        if item.TYPE == "show":
                            if RESET_SEASONS:
                                # get seasons
                                seasons = item.seasons()
                                blogger(
                                    f"-> Plex has {len(seasons)} seasons for: {item_title}",
                                    "info",
                                    "a",
                                    bar,
                                )
                                # loop over all:
                                for s in seasons:
                                    if id_array.count(f"{s.ratingKey}") == 0:
                                        item_title = get_log_title(s)
                                        # reset artwork
                                        blogger(
                                            f"-> getting season posters: {item_title}",
                                            "info",
                                            "a",
                                            bar,
                                        )
                                        posters = s.posters()
                                        blogger(
                                            f"-> Plex has {len(posters)} posters for: {item_title}",
                                            "info",
                                            "a",
                                            bar,
                                        )

                                        seasonPoster = pick_poster(posters, showPoster)

                                        apply_poster(s, seasonPoster)

                                        # Wait between items in case hammering the Plex server turns out badly.
                                        sleep_for_a_while()

                                        track_completion(
                                            id_array, status_file, f"{s.ratingKey}"
                                        )

                                    if RESET_EPISODES:
                                        # get episodes
                                        episodes = s.episodes()
                                        # loop over all
                                        for e in episodes:
                                            if id_array.count(f"{e.ratingKey}") == 0:
                                                item_title = get_log_title(e)
                                                # reset artwork
                                                blogger(
                                                    f"-> getting episode posters: {item_title}",
                                                    "info",
                                                    "a",
                                                    bar,
                                                )
                                                posters = e.posters()

                                                blogger(
                                                    f"-> Plex has {len(posters)} posters for: {item_title}",
                                                    "info",
                                                    "a",
                                                    bar,
                                                )

                                                episodePoster = pick_poster(
                                                    posters, None
                                                )

                                                apply_poster(e, episodePoster)

                                                # Wait between items in case hammering the Plex server turns out badly.
                                                sleep_for_a_while()

                                                track_completion(
                                                    id_array,
                                                    status_file,
                                                    f"{e.ratingKey}",
                                                )

                    except Exception as ex:
                        plogger(
                            f'Exception processing "{item.title}": {ex}', "info", "a"
                        )

                    bar()

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
plogger(
    f"{os.linesep}{os.linesep}processed {item_count - 1} items in {elapsed:.2f} seconds.",
    "info",
    "a",
)
