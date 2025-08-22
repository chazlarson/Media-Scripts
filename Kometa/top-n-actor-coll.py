import sys
import textwrap
from collections import Counter

from config import Config
from helpers import get_ids, get_plex, get_target_libraries
from tmdbapis import TMDbAPIs

config = Config('../config.yaml')

CAST_DEPTH = config.get_int("actor.cast_depth")
TOP_COUNT = config.get_int("actor.top_count")

DELAY = config.get_int('general.delay', 0)

tmdb = TMDbAPIs(str(config.get("general.tmdb_key", "NO_KEY_SPECIFIED")), language="en")

actors = Counter()

YAML_STR = ""
COLL_TMPL = ""

with open("template.tmpl") as tmpl:
    YAML_STR = tmpl.read()

with open("collection.tmpl") as tmpl:
    COLL_TMPL = tmpl.read()


def progress(count, total, status=""):
    bar_len = 40
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = "=" * filled_len + "-" * (bar_len - filled_len)
    stat_str = textwrap.shorten(status, width=30)

    sys.stdout.write("[%s] %s%s ... %s\r" % (bar, percents, "%", stat_str.ljust(30)))
    sys.stdout.flush()


plex = get_plex()

LIB_ARRAY = get_target_libraries(plex)

for lib in LIB_ARRAY:
    METADATA_TITLE = f"{lib} Top {TOP_COUNT} Actors.yml"

    print(f"getting items from [{lib}]...")
    items = plex.library.section(lib).all()
    item_total = len(items)
    print(f"looping over {item_total} items...")
    item_count = 1
    for item in items:
        tmpDict = {}
        imdbid, tmid, tvid = get_ids(item.guids)
        item_count = item_count + 1
        try:
            progress(item_count, item_total, item.title)
            cast = ""
            if item.TYPE == "show":
                cast = tmdb.tv_show(tmid).cast
            else:
                cast = tmdb.movie(tmid).casts["cast"]
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
