#!/usr/bin/env python
from datetime import datetime
from pathlib import Path

from alive_progress import alive_bar
from config import Config
from helpers import (get_all_from_library, get_ids, get_plex,
                     get_target_libraries)
from logs import blogger, logger, plogger, setup_logger
from tmdbapis import TMDbAPIs

SCRIPT_NAME = Path(__file__).stem

#      0.1.1 Log config details
#      0.1.2 incorporate helper changes, remove testing code
#      0.2.0 config class

VERSION = "0.2.0"

# current dateTime
now = datetime.now()

# convert to string
RUNTIME_STR = now.strftime("%Y-%m-%d %H:%M:%S")

ACTIVITY_LOG = f"{SCRIPT_NAME}.log"

setup_logger("activity_log", ACTIVITY_LOG)

plogger(f"Starting {SCRIPT_NAME} {VERSION} at {RUNTIME_STR}", "info", "a")

config = Config('../config.yaml')

plex = get_plex()

LIB_ARRAY = get_target_libraries(plex)

logger("connection success", "info", "a")

plogger(f"Adjusting future dates only: {config.get_bool("adjust_date.futures_only", False)}", "info", "a")

plogger(f"Adjusting epoch dates only: {config.get_bool("adjust_date.epoch_only", False)}", "info", "a")

EPOCH_DATE = datetime(1970, 1, 1, 0, 0, 0)

tmdb = TMDbAPIs(str(config.get("general.tmdb_key", "NO_KEY_SPECIFIED")), language="en")

def is_epoch(the_date):
    ret_val = False

    if the_date is not None:
        ret_val = the_date.year == 1970 and the_date.month == 1 and the_date.day == 1

    return ret_val


for lib in LIB_ARRAY:
    try:
        plogger(f"Loading {lib} ...", "info", "a")
        the_lib = plex.library.section(lib)
        is_movie = the_lib.type == "movie"
        is_show = the_lib.type == "show"

        if not is_movie:
            print("the script hasn't been tested with non-movie libraries, skipping.")
            # continue

        lib_size = the_lib.totalViewSize()

        if config.get_bool("adjust_date.futures_only", False):
            TODAY_STR = now.strftime("%Y-%m-%d")
            item_count, items = get_all_from_library(
                the_lib, None, {"addedAt>>": TODAY_STR}
            )
        else:
            item_count, items = get_all_from_library(the_lib)

        if item_count > 0:
            logger(f"looping over {item_count} items...", "info", "a")
            items_processed = 0

            plex_links = []
            external_links = []

            with alive_bar(
                item_count, dual_line=True, title=f"Adjust added dates {the_lib.title}"
            ) as bar:
                for item in items:
                    try:
                        items_processed += 1
                        added_too_far_apart = False
                        orig_too_far_apart = False
                        sub_items = [item]

                        if is_show:
                            episodes = item.episodes()
                            sub_items = sub_items + episodes

                        for sub_item in sub_items:
                            try:
                                imdbid, tmid, tvid = get_ids(sub_item.guids)

                                if is_movie:
                                    tmdb_item = tmdb.movie(tmid)
                                    release_date = tmdb_item.release_date
                                else:
                                    if sub_item.type == "show":
                                        tmdb_item = tmdb.tv_show(tmid)
                                        release_date = tmdb_item.first_air_date
                                    else:
                                        parent_show = sub_item.show()
                                        imdbid, tmid, tvid = get_ids(
                                            parent_show.guids
                                        )
                                        season_num = sub_item.seasonNumber
                                        episode_num = sub_item.episodeNumber

                                        tmdb_item = tmdb.tv_episode(
                                            tmid, season_num, episode_num
                                        )
                                        release_date = tmdb_item.air_date

                                added_date = item.addedAt
                                orig_date = item.originallyAvailableAt

                                if not config.get_bool("adjust_date.epoch_only", False) or (
                                    config.get_bool("adjust_date.epoch_only", False) and is_epoch(orig_date)
                                ):
                                    try:
                                        delta = added_date - release_date
                                        added_too_far_apart = abs(delta.days) > 1
                                    except:
                                        added_too_far_apart = (
                                            added_date is None
                                            and release_date is not None
                                        )

                                    try:
                                        delta = orig_date - release_date
                                        orig_too_far_apart = abs(delta.days) > 1
                                    except:
                                        orig_too_far_apart = (
                                            orig_date is None
                                            and release_date is not None
                                        )

                                    if added_too_far_apart:
                                        try:
                                            item.addedAt = release_date
                                            blogger(
                                                f"Set {sub_item.title} added at to {release_date}",
                                                "info",
                                                "a",
                                                bar,
                                            )
                                        except Exception as ex:
                                            plogger(
                                                f"Problem processing {item.title}; {ex}",
                                                "info",
                                                "a",
                                            )

                                    if orig_too_far_apart:
                                        try:
                                            item.originallyAvailableAt = release_date
                                            blogger(
                                                f"Set {sub_item.title} originally available at to {release_date}",
                                                "info",
                                                "a",
                                                bar,
                                            )
                                        except Exception as ex:
                                            plogger(
                                                f"Problem processing {item.title}; {ex}",
                                                "info",
                                                "a",
                                            )

                                else:
                                    blogger(
                                        f"skipping {item.title}: EPOCH_ONLY {config.get_bool("adjust_date.epoch_only", False)}, originally available date {orig_date}",
                                        "info",
                                        "a",
                                        bar,
                                    )

                            except Exception as ex:
                                plogger(
                                    f"Problem processing sub_item {item.title}; {ex}",
                                    "info",
                                    "a",
                                )

                    except Exception as ex:
                        plogger(f"Problem processing {item.title}; {ex}", "info", "a")

                    bar()

            plogger(f"Processed {items_processed} of {item_count}", "info", "a")

        progress_str = "COMPLETE"
        logger(progress_str, "info", "a")

    except Exception as ex:
        progress_str = f"Problem processing {lib}; {ex}"
        plogger(progress_str, "info", "a")
