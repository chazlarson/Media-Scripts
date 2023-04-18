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
            for actor in cast:
                if count < CAST_DEPTH:
                    count = count + 1
                    if actor.known_for_department == "Acting":
                        the_key = f"{actor.name} - {actor.person_id}"
                        actors[the_key] += 1
        except Exception as ex:
            progress(item_count, item_total, "EX: " + item.title)

    print("\r\r")

    count = 0
    for actor in sorted(actors.items(), key=lambda x: x[1], reverse=True):
        if count < TOP_COUNT:
            print("{}\t{}".format(actor[1], actor[0]))
            count = count + 1
