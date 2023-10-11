from collections import Counter
from datetime import datetime
from pathlib import Path
import platform
import time
from timeit import default_timer as timer
from alive_progress import alive_bar
from plexapi.server import PlexServer
import os
from dotenv import load_dotenv
import sys
import textwrap
from tmdbapis import TMDbAPIs

from helpers import booler, get_size, get_all_from_library, get_ids, get_letter_dir, get_plex, redact, validate_filename, load_and_upgrade_env
from logs import setup_logger, plogger, blogger, logger

# DONE 0.1.0: refactoring, added version

start = timer()

SCRIPT_NAME = Path(__file__).stem

VERSION = "0.1.0"

ACTIVITY_LOG = f"{SCRIPT_NAME}.log"

setup_logger('activity_log', ACTIVITY_LOG)

env_file_path = Path(".env")

# current dateTime
now = datetime.now()

IS_WINDOWS = platform.system() == "Windows"

# convert to string
RUNTIME_STR = now.strftime("%Y-%m-%d %H:%M:%S")

plogger(f"Starting {SCRIPT_NAME} {VERSION} at {RUNTIME_STR}", 'info', 'a')

if load_and_upgrade_env(env_file_path) < 0:
    exit()

LIBRARY_NAME = os.getenv("LIBRARY_NAME")
LIBRARY_NAMES = os.getenv("LIBRARY_NAMES")

if LIBRARY_NAMES:
    LIB_ARRAY = [s.strip() for s in LIBRARY_NAMES.split(",")]
else:
    LIB_ARRAY = [LIBRARY_NAME]

TMDB_KEY = os.getenv("TMDB_KEY")
TVDB_KEY = os.getenv("TVDB_KEY")
CAST_DEPTH = int(os.getenv("CAST_DEPTH"))
TOP_COUNT = int(os.getenv("TOP_COUNT"))
ACTORS_ONLY = booler(os.getenv("ACTORS_ONLY"))
TRACK_GENDER = booler(os.getenv("TRACK_GENDER"))

DELAY = int(os.getenv("DELAY"))

if not DELAY:
    DELAY = 0

tmdb = TMDbAPIs(TMDB_KEY, language="en")

tmdb_str = "tmdb://"
tvdb_str = "tvdb://"

actors = Counter()
casts = Counter()

def getTID(theList):
    tmid = None
    tvid = None
    for guid in theList:
        if tmdb_str in guid.id:
            tmid = guid.id.replace(tmdb_str, "")
        if tvdb_str in guid.id:
            tvid = guid.id.replace(tvdb_str, "")
    return tmid, tvid

plex = get_plex()

ALL_LIBS = plex.library.sections()
ALL_LIB_NAMES = []

plogger(f"{len(ALL_LIBS)} libraries found:", 'info', 'a')
for lib in ALL_LIBS:
    ALL_LIB_NAMES.append(f"{lib.title.strip()}")

if LIBRARY_NAMES == 'ALL_LIBRARIES':
    LIB_ARRAY = []
    for lib in ALL_LIBS:
        LIB_ARRAY.append(lib.title.strip())


for lib in LIB_ARRAY:
    print(f"getting items from [{lib}]...")
    the_lib = plex.library.section(lib)
    items = get_all_from_library(plex, the_lib)

    item_total = len(items)
    print(f"looping over {item_total} items...")
    item_count = 1
    cast_count = 0
    credit_count = 0
    skip_count = 0
    highwater_cast = 0
    total_cast = 0
    average_cast = 0
    with alive_bar(item_total, dual_line=True, title=f"Actor Count: {lib}") as bar:
        for item in items:
            tmpDict = {}
            tmdb_id, tvdb_id = getTID(item.guids)
            item_count = item_count + 1
            try:
                cast = ""
                if item.TYPE == "show":
                    cast = tmdb.tv_show(tmdb_id).cast
                else:
                    cast = tmdb.movie(tmdb_id).cast
                count = 0
                cast_size = len(cast)
                if cast_size < 2:
                    print(f"small cast - {item.title}: {cast_size}")
                casts[f"{cast_size}"] += 1
                total_cast += cast_size
                average_cast = round(total_cast / item_count)
                if cast_size > highwater_cast:
                    highwater_cast = cast_size
                    print(f"New cast size high water mark - {item.title}: {highwater_cast}")

                bar.text(f"Processing {CAST_DEPTH if CAST_DEPTH < cast_size else cast_size} of {cast_size} from {item.title} - average cast size {average_cast}")
                for actor in cast:
                    # actor points to person
                    gender = None
                    if TRACK_GENDER:
                        person = tmdb.person(actor.person_id)
                        gender = person.gender

                    if count < CAST_DEPTH:
                        count = count + 1
                        cast_count += 1
                        the_key = f"{actor.name} - {actor.person_id} - {gender}"
                        count_them = False
                        if ACTORS_ONLY:
                            if actor.known_for_department == "Acting":
                                count_them = True
                            else:
                                skip_count += 1
                                print(f"Skipping {actor.name}: {actor.known_for_department}")
                        else:
                            count_them = True

                        if count_them:
                            actors[the_key] += 1
                            credit_count += 1
            except Exception as ex:
                print(f"{item_count}, {item_total}, EX: {item.title}")

            bar()

            # Wait between items in case hammering the Plex server turns out badly.
            time.sleep(DELAY)

    print("\r\r")

    end = timer()
    elapsed = end - start
    print(f"Looked at {cast_count} credits from the top {CAST_DEPTH} from each {the_lib.TYPE} in {elapsed} seconds.")
    print(f"Unique people: {len(actors)}")
    print(f"Unique cast counts: {len(casts)}")
    print(f"Longest cast list: {highwater_cast}")
    print(f"Skipped {skip_count} non-actors")
    print(f"Total {credit_count} credits recorded")
    print(f"Top {TOP_COUNT} listed below")

    count = 0
    for actor in sorted(actors.items(), key=lambda x: x[1], reverse=True):
        if count < TOP_COUNT:
            print("{}\t{}".format(actor[1], actor[0]))
            count = count + 1
