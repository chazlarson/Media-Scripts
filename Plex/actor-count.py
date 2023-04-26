from collections import Counter
from plexapi.server import PlexServer
import os
from dotenv import load_dotenv
import sys
import textwrap
from tmdbapis import TMDbAPIs

from helpers import booler, get_size, get_all, get_ids, get_letter_dir, get_plex, redact, validate_filename

load_dotenv()

PLEX_URL = os.getenv("PLEX_URL")
PLEX_TOKEN = os.getenv("PLEX_TOKEN")
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


def progress(count, total, status=""):
    bar_len = 40
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = "=" * filled_len + "-" * (bar_len - filled_len)
    stat_str = textwrap.shorten(status, width=30)

    sys.stdout.write("[%s] %s%s ... %s\r" % (bar, percents, "%", stat_str.ljust(30)))
    sys.stdout.flush()


plex = get_plex(PLEX_URL, PLEX_TOKEN)

for lib in lib_array:
    print(f"getting items from [{lib}]...")
    the_lib = plex.library.section(lib)
    items = get_all(plex, the_lib)

    item_total = len(items)
    print(f"looping over {item_total} items...")
    item_count = 1
    cast_count = 0
    credit_count = 0
    skip_count = 0
    highwater_cast = 0
    total_cast = 0
    for item in items:
        tmpDict = {}
        tmdb_id, tvdb_id = getTID(item.guids)
        item_count = item_count + 1
        try:
            progress(item_count, item_total, item.title)
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
                print(f"New high water mark: {highwater_cast}")

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
