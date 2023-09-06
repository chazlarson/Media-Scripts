from collections import Counter
from datetime import datetime
from pathlib import Path
import platform
import time
from alive_progress import alive_bar
from plexapi.server import PlexServer
import os
from dotenv import load_dotenv
import sys
import textwrap
from tmdbapis import TMDbAPIs

from helpers import booler, get_size, get_all_from_library, get_ids, get_letter_dir, get_plex, redact, validate_filename, load_and_upgrade_env

# DONE 0.1.0: refactoring, added version

SCRIPT_NAME = Path(__file__).stem

VERSION = "0.1.0"

env_file_path = Path(".env")

# current dateTime
now = datetime.now()

IS_WINDOWS = platform.system() == "Windows"

# convert to string
RUNTIME_STR = now.strftime("%Y-%m-%d %H:%M:%S")

print(f"Starting {SCRIPT_NAME} {VERSION} at {RUNTIME_STR}", 'info', 'a')

if load_and_upgrade_env(env_file_path) < 0:
    exit()

LIBRARY_NAME = os.getenv("LIBRARY_NAME")
LIBRARY_NAMES = os.getenv("LIBRARY_NAMES")
TMDB_KEY = os.getenv("TMDB_KEY")
TVDB_KEY = os.getenv("TVDB_KEY")
CAST_DEPTH = int(os.getenv("CAST_DEPTH"))
TOP_COUNT = int(os.getenv("TOP_COUNT"))
ACTORS_ONLY = booler(os.getenv("ACTORS_ONLY"))
DELAY = int(os.getenv("DELAY"))

if not DELAY:
    DELAY = 0

if LIBRARY_NAMES:
    lib_array = LIBRARY_NAMES.split(",")
else:
    lib_array = [LIBRARY_NAME]

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

for lib in lib_array:
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
    with alive_bar(item_total, dual_line=True, title='Collection list - Plex') as bar:
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
                    print(f"{item.title}: {cast_size}")
                casts[f"{cast_size}"] += 1
                total_cast += cast_size
                if cast_size > highwater_cast:
                    highwater_cast = cast_size
                    print(f"New cast size high water mark: {highwater_cast}")

                for actor in cast:
                    if count < CAST_DEPTH:
                        count = count + 1
                        cast_count += 1
                        the_key = f"{actor.name} - {actor.person_id}"
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
                progress(item_count, item_total, "EX: " + item.title)

            bar()

            # Wait between items in case hammering the Plex server turns out badly.
            time.sleep(DELAY)

    print("\r\r")

    print(f"Looked at {cast_count} credits from the top {CAST_DEPTH} from each {the_lib.TYPE}")
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
