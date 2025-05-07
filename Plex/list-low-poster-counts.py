#!/usr/bin/env python
import os
import platform
from datetime import datetime
from pathlib import Path

from alive_progress import alive_bar
from helpers import get_all_from_library, get_plex, load_and_upgrade_env
from logs import logger, plogger, setup_logger

SCRIPT_NAME = Path(__file__).stem

VERSION = "0.1.0"

env_file_path = Path(".env")

# current dateTime
now = datetime.now()

IS_WINDOWS = platform.system() == "Windows"

# convert to string
RUNTIME_STR = now.strftime("%Y-%m-%d %H:%M:%S")

ACTIVITY_LOG = f"{SCRIPT_NAME}.log"
DOWNLOAD_LOG = f"{SCRIPT_NAME}-dl.log"

setup_logger("activity_log", ACTIVITY_LOG)

plogger(f"Starting {SCRIPT_NAME} {VERSION} at {RUNTIME_STR}", "info", "a")

if load_and_upgrade_env(env_file_path) < 0:
    exit()

ID_FILES = True

URL_ARRAY = []
# no one using this yet
# QUEUED_DOWNLOADS = {}

target_url_var = "PLEX_URL"
PLEX_URL = os.getenv(target_url_var)
if PLEX_URL is None:
    target_url_var = "PLEXAPI_AUTH_SERVER_BASEURL"
    PLEX_URL = os.getenv(target_url_var)

target_token_var = "PLEX_TOKEN"
PLEX_TOKEN = os.getenv(target_token_var)
if PLEX_TOKEN is None:
    target_token_var = "PLEXAPI_AUTH_SERVER_TOKEN"
    PLEX_TOKEN = os.getenv(target_token_var)

if PLEX_URL is None or PLEX_URL == "https://plex.domain.tld":
    plogger(f"You must specify {target_url_var} in the .env file.", "info", "a")
    exit()

if PLEX_TOKEN is None or PLEX_TOKEN == "PLEX-TOKEN":
    plogger(f"You must specify {target_token_var} in the .env file.", "info", "a")
    exit()

LIBRARY_NAME = os.getenv("LIBRARY_NAME")
LIBRARY_NAMES = os.getenv("LIBRARY_NAMES")

SUPERCHAT = os.getenv("SUPERCHAT")

DELAY = int(os.getenv("DELAY"))

if not DELAY:
    DELAY = 0

POSTER_THRESHOLD = int(os.getenv("POSTER_THRESHOLD"))

if LIBRARY_NAMES:
    LIB_ARRAY = [s.strip() for s in LIBRARY_NAMES.split(",")]
else:
    LIB_ARRAY = [LIBRARY_NAME]

imdb_str = "imdb://"
tmdb_str = "tmdb://"
tvdb_str = "tvdb://"

redaction_list = []
redaction_list.append(os.getenv("PLEXAPI_AUTH_SERVER_BASEURL"))
redaction_list.append(os.getenv("PLEXAPI_AUTH_SERVER_TOKEN"))

plex = get_plex()

logger("Plex connection succeeded", "info", "a")


def lib_type_supported(lib):
    return lib.type == "movie" or lib.type == "show"


ALL_LIBS = plex.library.sections()
ALL_LIB_NAMES = []

logger(f"{len(ALL_LIBS)} libraries found:", "info", "a")
for lib in ALL_LIBS:
    logger(
        f"{lib.title.strip()}: {lib.type} - supported: {lib_type_supported(lib)}",
        "info",
        "a",
    )
    ALL_LIB_NAMES.append(f"{lib.title.strip()}")

if LIBRARY_NAMES == "ALL_LIBRARIES":
    LIB_ARRAY = []
    for lib in ALL_LIBS:
        if lib_type_supported(lib):
            LIB_ARRAY.append(lib.title.strip())

TOPLEVEL_TMID = ""
TOPLEVEL_TVID = ""


def get_lib_setting(the_lib, the_setting):
    settings = the_lib.settings()
    for setting in settings:
        if setting.id == the_setting:
            return setting.value


for lib in LIB_ARRAY:
    if lib in ALL_LIB_NAMES:
        try:
            highwater = 0

            plogger(f"Loading {lib} ...", "info", "a")
            the_lib = plex.library.section(lib)
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

        except Exception as ex:
            progress_str = f"Problem processing {lib}; {ex}"
            plogger(progress_str, "info", "a")
    else:
        logger(
            f"Library {lib} not found: available libraries on this server are: {ALL_LIB_NAMES}",
            "info",
            "a",
        )

plogger("Complete!", "info", "a")
