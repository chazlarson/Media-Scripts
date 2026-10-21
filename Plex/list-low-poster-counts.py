#!/usr/bin/env python
import platform
from datetime import datetime
from pathlib import Path

from alive_progress import alive_bar
from config import Config
from helpers import (get_all_from_library, get_plex, get_redaction_list,
                     get_target_libraries)
from logs import logger, plogger, setup_logger

config = Config('../config.yaml')

SCRIPT_NAME = Path(__file__).stem

VERSION = "0.1.0"

# current dateTime
now = datetime.now()

IS_WINDOWS = platform.system() == "Windows"

# convert to string
RUNTIME_STR = now.strftime("%Y-%m-%d %H:%M:%S")

ACTIVITY_LOG = f"{SCRIPT_NAME}.log"
DOWNLOAD_LOG = f"{SCRIPT_NAME}-dl.log"

setup_logger("activity_log", ACTIVITY_LOG)

plogger(f"Starting {SCRIPT_NAME} {VERSION} at {RUNTIME_STR}", "info", "a")

ID_FILES = True

URL_ARRAY = []
# no one using this yet
# QUEUED_DOWNLOADS = {}

SUPERCHAT = config.get("general.superchat", False)

DELAY = config.get_int("general.delay", 0)

POSTER_THRESHOLD = config.get_int("low_poster_count.poster_threshold", 5)

redaction_list = get_redaction_list()

plex = get_plex()

LIB_ARRAY = get_target_libraries(plex)

def lib_type_supported(lib):
    return lib.type == "movie" or lib.type == "show"


def get_lib_setting(the_lib, the_setting):
    settings = the_lib.settings()
    for setting in settings:
        if setting.id == the_setting:
            return setting.value


for lib in LIB_ARRAY:
    try:
        highwater = 0

        plogger(f"Loading {lib} ...", "info", "a")
        the_lib = plex.library.section(lib)
        if lib_type_supported(the_lib):
            the_uuid = the_lib.uuid
            ID_ARRAY = []
            the_title = the_lib.title

            item_total, items = get_all_from_library(the_lib, None, None)
            plogger(
                f"Completed loading {item_total} of {the_lib.totalViewSize()} {the_lib.TYPE}(s) from {the_lib.title}",
                "info",
                "a",
            )

            if item_total > 0:
                logger(f"looping over {item_total} items...", "info", "a")
                item_count = 0

                plex_links = []
                external_links = []

                with alive_bar(
                    item_total,
                    dual_line=True,
                    title=f"Low poster counts {the_lib.title}",
                ) as bar:
                    for item in items:
                        try:
                            all_posters = item.posters()
                            if len(all_posters) < POSTER_THRESHOLD:
                                plogger(
                                    f"{item.title} poster count: {len(all_posters)}",
                                    "info",
                                    "a",
                                )

                            item_count += 1
                        except Exception as ex:
                            plogger(
                                f"Problem processing {item.title}; {ex}", "info", "a"
                            )

                        bar()

                plogger(f"Processed {item_count} of {item_total}", "info", "a")

            progress_str = "COMPLETE"
            logger(progress_str, "info", "a")
        else:
            print(f"Library type '{the_lib.type}' not supported")

    except Exception as ex:
        progress_str = f"Problem processing {lib}; {ex}"
        plogger(progress_str, "info", "a")

plogger("Complete!", "info", "a")
