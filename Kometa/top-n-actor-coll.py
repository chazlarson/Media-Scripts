import os
import sys
import textwrap
from collections import Counter

from dotenv import load_dotenv
from plexapi.server import PlexServer
from tmdbapis import TMDbAPIs

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

YAML_STR = ""
COLL_TMPL = ""

with open("template.tmpl") as tmpl:
    YAML_STR = tmpl.read()

with open("collection.tmpl") as tmpl:
    COLL_TMPL = tmpl.read()


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


print(f"connecting to {PLEX_URL}...")
plex = PlexServer(PLEX_URL, PLEX_TOKEN)
for lib in lib_array:
    METADATA_TITLE = f"{lib} Top {TOP_COUNT} Actors.yml"

    print(f"getting items from [{lib}]...")
    items = plex.library.section(lib).all()
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
                cast = tmdb.movie(tmdb_id).casts["cast"]
            count = 0
            for actor in cast:
                if count < CAST_DEPTH:
                    count = count + 1
                    if actor.known_for_department == "Acting":
                        tmpDict[f"{actor.id}-{actor.name}"] = 1
            actors.update(tmpDict)
        except Exception:
            progress(item_count, item_total, "EX: " + item.title)

    print("\r\r")

    count = 0
    for actor in sorted(actors.items(), key=lambda x: x[1], reverse=True):
        if count < TOP_COUNT:
            print("{}\t{}".format(actor[1], actor[0]))
            name_arr = actor[0].split("-")
            this_coll = COLL_TMPL.replace("%%NAME%%", name_arr[1])
            this_coll = this_coll.replace("%%ID%%", name_arr[0])
            YAML_STR = YAML_STR + this_coll
            count = count + 1

    with open(METADATA_TITLE, "w") as out:
        out.write(YAML_STR)
