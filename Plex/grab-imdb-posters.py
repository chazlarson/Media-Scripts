#!/usr/bin/env python
import logging
import os
import sys
import textwrap
from datetime import datetime
from pathlib import Path

import imdb
from config import Config
from helpers import get_ids, get_plex, get_redaction_list, get_target_libraries

# current dateTime
now = datetime.now()

# convert to string
RUNTIME_STR = now.strftime("%Y-%m-%d %H:%M:%S")

SCRIPT_NAME = Path(__file__).stem

VERSION = "0.1.0"

logging.basicConfig(
    filename=f"{SCRIPT_NAME}.log",
    filemode="w",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logging.info(f"Starting {SCRIPT_NAME} {VERSION} at {RUNTIME_STR}", "info", "a")
print(f"Starting {SCRIPT_NAME} {VERSION} at {RUNTIME_STR}", "info", "a")

config = Config('../config.yaml')

POSTER_CONSOLIDATE = config.get_bool("image_download.general.poster_consolidate")

if config.get_bool("image_download.general.poster_download"):
    script_string = f'#!/bin/bash{os.linesep}{os.linesep}# SCRIPT TO DO STUFF{os.linesep}{os.linesep}cd "{config.get("image_download.where_to_put_it.poster_dir")}"{os.linesep}{os.linesep}'
else:
    script_string = ""


def progress(count, total, status=""):
    bar_len = 40
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = "=" * filled_len + "-" * (bar_len - filled_len)
    stat_str = textwrap.shorten(status, width=80)

    sys.stdout.write("[%s] %s%s ... %s\r" % (bar, percents, "%", stat_str.ljust(80)))
    sys.stdout.flush()


all_items = []

plex = get_plex()

LIB_ARRAY = get_target_libraries(plex)

logging.info("connection success")

for lib in LIB_ARRAY:
    print(f"getting items from [{lib}]...")
    items = plex.library.section(lib).all()
    item_total = len(items)
    print(f"looping over {item_total} items...")
    item_count = 0

    plex_links = []
    external_links = []

    for item in items:
        item_count = item_count + 1
        imdb_id, tmdb_id, tvdb_id = get_ids(item.guids, TMDB_KEY)

        tmpDict = {}
        tmpDict["title"] = item.title
        tmpDict["ratingKey"] = item.ratingKey
        tmpDict["imdb"] = imdb_id
        tmpDict["tmdb"] = tmdb_id
        tmpDict["tvdb"] = tvdb_id
        all_items.append(tmpDict)

        progress_str = f"{item.title}"
        progress(item_count, item_total, progress_str)

    print("{os.linesep}")

print("processing items...")
item_total = len(all_items)
print(f"looping over {item_total} items...")
item_count = 0

# creating instance of IMDb
ia = imdb.IMDb()

for item in all_items:
    item_count = item_count + 1

    progress_str = f"{item['title']}"
    progress(item_count, item_total, progress_str)

    # id
    code = "6468322"
    imdid = item["imdb"].replace("tt", "")

    # getting information
    series = ia.get_movie(imdid)

    # getting cover url of the series
    cover = series.data["cover url"]
