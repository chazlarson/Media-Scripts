""" module generates actor collections """
from collections import Counter
import os
import sys
import textwrap
from tmdbapis import TMDbAPIs
from dotenv import load_dotenv
from plexapi.server import PlexServer

load_dotenv()

plex_url = os.getenv("PLEX_URL")
plex_token = os.getenv("PLEX_TOKEN")
LIBRARY_NAME = os.getenv("LIBRARY_NAME")
LIBRARY_NAMES = os.getenv("LIBRARY_NAMES")
tmdb_key = os.getenv("TMDB_KEY")
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

tmdb = TMDbAPIs(tmdb_key, language="en")

TMDB_STR = "tmdb://"
TVDB_STR = "tvdb://"

actors = Counter()

YAML_STR = ""
COLL_TMPL = ""

with open("template.tmpl") as tmpl: # pylint: disable=unspecified-encoding
    YAML_STR = tmpl.read()

with open("collection.tmpl") as tmpl: # pylint: disable=unspecified-encoding
    COLL_TMPL = tmpl.read()


def get_tid(the_list):
    """ get tmdb and tvdb ids """
    tmid = None
    tvid = None
    for guid in the_list:
        if TMDB_STR in guid.id:
            tmid = guid.id.replace(TMDB_STR, "")
        if TVDB_STR in guid.id:
            tvid = guid.id.replace(TVDB_STR, "")
    return tmid, tvid


def progress(counter, total, status=""):
    """ draw progress bar """
    bar_len = 40
    filled_len = int(round(bar_len * counter / float(total)))

    percents = round(100.0 * counter / float(total), 1)
    p_bar = "=" * filled_len + "-" * (bar_len - filled_len)
    stat_str = textwrap.shorten(status, width=30)

    sys.stdout.write(f"[{p_bar}] {percents}% ... {stat_str.ljust(30)}\r")
    sys.stdout.flush()


print(f"connecting to {plex_url}...")
plex = PlexServer(plex_url, plex_token)
for lib in lib_array:
    METADATA_TITLE = f"{lib} Top {TOP_COUNT} Actors.yml"

    print(f"getting items from [{lib}]...")
    items = plex.library.section(lib).all()
    item_total = len(items)
    print(f"looping over {item_total} items...")
    ITEM_COUNT = 1
    for item in items:
        tmpDict = {}
        tmdb_id, tvdb_id = get_tid(item.guids)
        ITEM_COUNT = ITEM_COUNT + 1
        try:
            progress(ITEM_COUNT, item_total, item.title)
            CAST = ""
            if item.TYPE == "show":
                CAST = tmdb.tv_show(tmdb_id).cast
            else:
                CAST = tmdb.movie(tmdb_id).casts["cast"]
            COUNT = 0
            for actor in CAST:
                if COUNT < CAST_DEPTH:
                    COUNT = COUNT + 1
                    if actor.known_for_department == "Acting":
                        tmpDict[f"{actor.id}-{actor.name}"] = 1
            actors.update(tmpDict)
        except Exception as ex: # pylint: disable=broad-exception-caught
            progress(ITEM_COUNT, item_total, "EX: " + item.title)

    print("\r\r")

    COUNT = 0
    for actor in sorted(actors.items(), key=lambda x: x[1], reverse=True):
        if COUNT < TOP_COUNT:
            print(f"{actor[1]}\t{actor[0]}")
            name_arr = actor[0].split("-")
            this_coll = COLL_TMPL.replace("%%NAME%%", name_arr[1])
            this_coll = this_coll.replace("%%ID%%", name_arr[0])
            YAML_STR = YAML_STR + this_coll
            COUNT = COUNT + 1

    with open(METADATA_TITLE, "w", encoding="utf-8") as out:
        out.write(YAML_STR)
