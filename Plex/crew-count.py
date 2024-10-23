from collections import Counter
from plexapi.server import PlexServer
import os
from dotenv import load_dotenv
import sys
import textwrap
from tmdbapis import TMDbAPIs
from helpers import booler

load_dotenv()

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

tmdb = TMDbAPIs(TMDB_KEY, language="en")

TMDB_STR = "tmdb://"
TVDB_STR = "tvdb://"

individuals = Counter()
jobs = Counter()

YAML_STR = ""
COLL_TMPL = ""


def getTID(the_list):
    tmid = None
    tvid = None
    for guid in the_list:
        if TMDB_STR in guid.id:
            tmid = guid.id.replace(TMDB_STR, "")
        if TVDB_STR in guid.id:
            tvid = guid.id.replace(TVDB_STR, "")
    return tmid, tvid


def progress(count, total, status=""):
    bar_len = 40
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = "=" * filled_len + "-" * (bar_len - filled_len)
    stat_str = textwrap.shorten(status, width=30)

    sys.stdout.write("[%s] %s%s ... %s\r" % (bar, percents, "%", stat_str.ljust(30)))
    sys.stdout.flush()

print(f"connecting to Plex...")
plex = PlexServer(PLEX_URL, PLEX_TOKEN)
for lib in lib_array:
    print(f"getting items from [{lib}]...")
    items = plex.library.section(lib).all()
    item_total = len(items)
    print(f"looping over {item_total} items...")
    item_count = 1
    for item in items:
        jobDict = {}
        tmpDict = {}
        tmdb_id, tvdb_id = getTID(item.guids)
        item_count = item_count + 1
        try:
            progress(item_count, item_total, item.title)
            crew = None
            if item.TYPE == "show":
                crew = tmdb.tv_show(tmdb_id).crew
            else:
                crew = tmdb.movie(tmdb_id).crew
            count = 0
            for individual in crew:
                if count < CREW_DEPTH:
                    count = count + 1
                    if individual.job == TARGET_JOB:
                        tmpDict[f"{individual.name} - {individual.person_id}"] = 1
                    if SHOW_JOBS:
                        jobDict[f"{individual.job}"] = 1

            individuals.update(tmpDict)
            jobs.update(jobDict)
        except Exception as ex:
            progress(item_count, item_total, "EX: " + item.title)

    print("\r\r")

    FOUND_COUNT = len(individuals.items())
    count = 0
    print(f"Top {FOUND_COUNT if FOUND_COUNT < CREW_COUNT else CREW_COUNT} {TARGET_JOB} in [{lib}]:")
    for individual in sorted(individuals.items(), key=lambda x: x[1], reverse=True):
        if count < CREW_COUNT:
            print("{}\t{}".format(individual[1], individual[0]))
            count = count + 1

    JOB_COUNT = len(jobs.items())
    count = 0
    print(f"{JOB_COUNT} defined [{lib}]:")
    for job in sorted(jobs.items(), key=lambda x: x[1], reverse=True):
        print("{}\t{}".format(job[1], job[0]))
