import sys
import textwrap
from collections import Counter

from config import Config
from helpers import get_ids, get_plex, get_redaction_list, get_target_libraries
from tmdbapis import TMDbAPIs

config = Config('../config.yaml')

CREW_COUNT = config.get_int('crew.count')
TARGET_JOB = config.get('crew.target_job')
DELAY = config.get_int('general.delay')
SHOW_JOBS = config.get_bool('crew.show_jobs')

if not DELAY:
    DELAY = 0


tmdb = TMDbAPIs(str(config.get("general.tmdb_key", "NO_KEY_SPECIFIED")), language="en")

individuals = Counter()
jobs = Counter()

YAML_STR = ""
COLL_TMPL = ""


def progress(count, total, status=""):
    bar_len = 40
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = "=" * filled_len + "-" * (bar_len - filled_len)
    stat_str = textwrap.shorten(status, width=30)

    sys.stdout.write("[%s] %s%s ... %s\r" % (bar, percents, "%", stat_str.ljust(30)))
    sys.stdout.flush()


plex = get_plex()

lib_array = get_target_libraries(plex)

for lib in lib_array:
    print(f"getting items from [{lib}]...")
    items = plex.library.section(lib).all()
    item_total = len(items)
    print(f"looping over {item_total} items...")
    item_count = 1
    for item in items:
        jobDict = {}
        tmpDict = {}
        imdbid, tmid, tvid = get_ids(item.guids)
        item_count = item_count + 1
        try:
            progress(item_count, item_total, item.title)
            crew = None
            if item.TYPE == "show":
                crew = tmdb.tv_show(tmid).crew
            else:
                crew = tmdb.movie(tmid).crew
            count = 0
            for individual in crew:
                if count <  config.get_int('crew.depth'):
                    count = count + 1
                    if individual.job == TARGET_JOB:
                        tmpDict[f"{individual.name} - {individual.person_id}"] = 1
                    if SHOW_JOBS:
                        jobDict[f"{individual.job}"] = 1

            individuals.update(tmpDict)
            jobs.update(jobDict)
        except Exception:
            progress(item_count, item_total, "EX: " + item.title)

    print("\r\r")

    FOUND_COUNT = len(individuals.items())
    count = 0
    print(
        f"Top {FOUND_COUNT if FOUND_COUNT < CREW_COUNT else CREW_COUNT} {TARGET_JOB} in [{lib}]:"
    )
    for individual in sorted(individuals.items(), key=lambda x: x[1], reverse=True):
        if count < CREW_COUNT:
            print("{}\t{}".format(individual[1], individual[0]))
            count = count + 1

    JOB_COUNT = len(jobs.items())
    count = 0
    print(f"{JOB_COUNT} jobs defined [{lib}]:")
    for job in sorted(jobs.items(), key=lambda x: x[1], reverse=True):
        print("{}\t{}".format(job[1], job[0]))
