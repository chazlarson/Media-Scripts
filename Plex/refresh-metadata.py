#!/usr/bin/env python
import logging
import os
import sys
import textwrap
import time
from datetime import datetime
from pathlib import Path

import urllib3.exceptions
from alive_progress import alive_bar
from config import Config
from helpers import (get_all_from_library, get_plex, get_redaction_list,
                     get_target_libraries)
from logs import logger, plogger, setup_logger
from requests import ReadTimeout
from urllib3.exceptions import ReadTimeoutError

# current dateTime
now = datetime.now()

# convert to string
RUNTIME_STR = now.strftime("%Y-%m-%d %H:%M:%S")

SCRIPT_NAME = Path(__file__).stem

VERSION = "0.1.0"

ACTIVITY_LOG = f"{SCRIPT_NAME}.log"
setup_logger("activity_log", ACTIVITY_LOG)

plogger(f"Starting {SCRIPT_NAME} {VERSION} at {RUNTIME_STR}", "info", "a")

config = Config('../config.yaml')

plex = get_plex()

LIB_ARRAY = get_target_libraries(plex)

DELAY = config.get_int('general.delay', 0)
REFRESH_1970_ONLY = config.get_bool('refresh_metadata.refresh_1970_only', False)


def progress(count, total, status=""):
    bar_len = 40
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = "=" * filled_len + "-" * (bar_len - filled_len)
    stat_str = textwrap.shorten(status, width=80)

    sys.stdout.write("[%s] %s%s ... %s\r" % (bar, percents, "%", stat_str.ljust(80)))
    sys.stdout.flush()


for lib in LIB_ARRAY:
    print(f"getting items from [{lib}]...")
    logger(f"getting items from [{lib}]...", "info", "a")
    the_lib = plex.library.section(lib)
    item_total, items = get_all_from_library(the_lib)
    logger(f"looping over {item_total} items...", "info", "a")
    item_count = 1

    plex_links = []
    external_links = []

    with alive_bar(
        item_total, dual_line=True, title=f"Refresh Metadata: {the_lib.title}"
    ) as bar:
        for item in items:
            tmpDict = {}
            item_count = item_count + 1
            attempts = 0

            progress_str = f"{item.title}"

            progress(item_count, item_total, progress_str)

            while attempts < 5:
                try:
                    progress_str = f"{item.title} - attempt {attempts + 1}"
                    logger(progress_str, "info", "a")

                    item.refresh()

                    time.sleep(DELAY)
                    progress_str = f"{item.title} - DONE"
                    progress(item_count, item_total, progress_str)

                    attempts = 6
                except urllib3.exceptions.ReadTimeoutError:
                    progress(item_count, item_total, "ReadTimeoutError: " + item.title)
                except urllib3.exceptions.HTTPError:
                    progress(item_count, item_total, "HTTPError: " + item.title)
                except ReadTimeoutError:
                    progress(
                        item_count, item_total, "ReadTimeoutError-2: " + item.title
                    )
                except ReadTimeout:
                    progress(item_count, item_total, "ReadTimeout: " + item.title)
                except Exception as ex:
                    progress(item_count, item_total, "EX: " + item.title)
                    logging.error(ex)

                attempts += 1

    print(os.linesep)
