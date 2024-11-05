""" Count the number of crew members in a Plex library """
import logging
import os
import sys
import textwrap
from datetime import datetime
from pathlib import Path
from collections import Counter
from tmdbapis import TMDbAPIs
from plexapi.server import PlexServer
from helpers import booler, get_ids, get_plex, load_and_upgrade_env

# current dateTime
now = datetime.now()

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

logging.info(f"Starting {SCRIPT_NAME} {VERSION} at {RUNTIME_STR}")
print(f"Starting {SCRIPT_NAME} {VERSION} at {RUNTIME_STR}")

if load_and_upgrade_env(env_file_path) < 0:
    sys.exit() 

plex_url = os.getenv("PLEX_URL")
plex_token = os.getenv("PLEX_TOKEN")
LIBRARY_NAME = os.getenv("LIBRARY_NAME")
LIBRARY_NAMES = os.getenv("LIBRARY_NAMES")
tmdb_key = os.getenv("TMDB_KEY")
TVDB_KEY = os.getenv("TVDB_KEY")
CREW_DEPTH = int(os.getenv("CREW_DEPTH"))
CREW_COUNT = int(os.getenv("CREW_COUNT"))
TARGET_JOB = os.getenv("TARGET_JOB")
DELAY = int(os.getenv("DELAY"))
SHOW_JOBS = booler(os.getenv("SHOW_JOBS"))

if not DELAY:
    DELAY = 0

if LIBRARY_NAMES:
    lib_array = LIBRARY_NAMES.split(",")
else:
    lib_array = [LIBRARY_NAME]

tmdb = TMDbAPIs(tmdb_key, language="en")

TMDB_STR = "tmdb://"
TVDB_STR = "tvdb://"

individuals = Counter()
jobs = Counter()

YAML_STR = ""
COLL_TMPL = ""

def progress(counter, total, status=""):
    """ Progress bar """
    bar_len = 40
    filled_len = int(round(bar_len * counter / float(total)))

    percents = round(100.0 * counter / float(total), 1)
    p_bar = "=" * filled_len + "-" * (bar_len - filled_len)
    stat_str = textwrap.shorten(status, width=30)

    tmp_str = f"[{p_bar}] {percents}% ... {stat_str.ljust(30)}\r"
    sys.stdout.write(tmp_str)
    sys.stdout.flush()

print("connecting to Plex...")
plex = get_plex()

for lib in lib_array:
    print(f"getting items from [{lib}]...")
    items = plex.library.section(lib).all()
    item_total = len(items)
    print(f"looping over {item_total} items...")
    ITEM_COUNT = 1
    for item in items:
        jobDict = {}
        tmpDict = {}
        imdb_id, tmdb_id, tvdb_id = get_ids(item.guids) # pylint: disable=unused-variable
        ITEM_COUNT = ITEM_COUNT + 1
        try:
            progress(ITEM_COUNT, item_total, item.title)
            CREW = None
            if item.TYPE == "show":
                CREW = tmdb.tv_show(tmdb_id).crew
            else:
                CREW = tmdb.movie(tmdb_id).crew
            COUNT = 0
            for individual in CREW:
                if COUNT < CREW_DEPTH:
                    COUNT = COUNT + 1
                    if individual.job == TARGET_JOB:
                        tmpDict[f"{individual.name} - {individual.person_id}"] = 1
                    if SHOW_JOBS:
                        jobDict[f"{individual.job}"] = 1

            individuals.update(tmpDict)
            jobs.update(jobDict)
        except Exception as ex: # pylint: disable=broad-exception-caught
            progress(ITEM_COUNT, item_total, "EX: " + item.title)

    print("\r\r")

    FOUND_COUNT = len(individuals.items())
    COUNT = 0
    print(f"Top {FOUND_COUNT if FOUND_COUNT < CREW_COUNT else CREW_COUNT} {TARGET_JOB} in [{lib}]:")
    for individual in sorted(individuals.items(), key=lambda x: x[1], reverse=True):
        if COUNT < CREW_COUNT:
            print(f"{individual[1]}\t{individual[0]}")
            COUNT = COUNT + 1

    JOB_COUNT = len(jobs.items())
    COUNT = 0
    print(f"{JOB_COUNT} defined [{lib}]:")
    for job in sorted(jobs.items(), key=lambda x: x[1], reverse=True):
        print(f"{job[1]}\t{job[0]}")
