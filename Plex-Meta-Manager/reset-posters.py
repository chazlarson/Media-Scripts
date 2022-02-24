from plexapi.server import PlexServer
import os
from dotenv import load_dotenv
import sys
import textwrap
from tmdbapis import TMDbAPIs
import requests
import pathlib
from timeit import default_timer as timer
import time

# import tvdb_v4_official

start = timer()

load_dotenv()

PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')
LIBRARY_NAME = os.getenv('LIBRARY_NAME')
LIBRARY_NAMES = os.getenv('LIBRARY_NAMES')
TMDB_KEY = os.getenv('TMDB_KEY')
TVDB_KEY = os.getenv('TVDB_KEY')
REMOVE_LABELS = os.getenv('REMOVE_LABELS')
DELAY = os.getenv('DELAY')

if not DELAY:
    DELAY = 0

if REMOVE_LABELS:
    lbl_array = REMOVE_LABELS.split(",")

if LIBRARY_NAMES:
    lib_array = LIBRARY_NAMES.split(",")
else:
    lib_array = [LIBRARY_NAME]

# Commented out until this doesn't throw a 400
# tvdb = tvdb_v4_official.TVDB(TVDB_KEY)

tmdb = TMDbAPIs(TMDB_KEY, language="en")

tmdb_str = 'tmdb://'
tvdb_str = 'tvdb://'

local_dir = f"{os.getcwd()}/posters"

os.makedirs(local_dir, exist_ok=True)

show_dir = f"{local_dir}/shows"
movie_dir = f"{local_dir}/movies"

os.makedirs(show_dir, exist_ok=True)
os.makedirs(movie_dir, exist_ok=True)

def removeLabels(theItem):
    for lbl in lbl_array:
        theItem.removeLabel(lbl, True)
    # for label in theItem.labels:
    #     for lbl in lbl_array:
    #         if label.tag == lbl:
    #             theItem.removeLabel(lbl, True)

def getTID(theList):
    tmid = None
    tvid = None
    for guid in theList:
        if tmdb_str in guid.id:
            tmid = guid.id.replace(tmdb_str,'')
        if tvdb_str in guid.id:
            tvid = guid.id.replace(tvdb_str,'')
    return tmid, tvid

def progress(count, total, status=''):
    bar_len = 40
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)
    stat_str = textwrap.shorten(status, width=30)

    sys.stdout.write('[%s] %s%s ... %s\r' % (bar, percents, '%', stat_str.ljust(30)))
    sys.stdout.flush()

print("tmdb config...")

base_url = tmdb.configuration().secure_base_image_url
size_str = 'original'

print(f"connecting to {PLEX_URL}...")
plex = PlexServer(PLEX_URL, PLEX_TOKEN)
for lib in lib_array:
    print(f"\ngetting items from [{lib}]...")
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
            pp = None
            if item.TYPE == 'show':
                try:
                    pp = tmdb.tv_show(tmdb_id).poster_path if tmdb_id else tmdb.find_by_id(tvdb_id=tvdb_id).tv_results[0].poster_path
                except:
                    pp = "NONE"
                tgt_dir = show_dir
            else:
                pp = tmdb.movie(tmdb_id).poster_path
                tgt_dir = movie_dir

            if pp is not None:
                if pp == "NONE":
                    posters = item.posters()
                    item.setPoster(posters[0])
                else:
                    ext = pathlib.Path(pp).suffix
                    posterURL = f"{base_url}{size_str}{pp}"
                    local_file = f"{tgt_dir}/{item.ratingKey}{ext}"
                    if not os.path.exists(local_file):
                        r = requests.get(posterURL, allow_redirects=True)
                        open(f"{local_file}", 'wb').write(r.content)
                    item.uploadPoster(filepath=local_file)
            else:
                progress(item_count, item_total, "unknown type: " + item.title)

            if len(lbl_array) > 0:
                removeLabels(item)

        except Exception as ex:
            progress(item_count, item_total, "EX: " + item.title)

        # Wait between items in case hammering the Plex server turns out badly.
        time.sleep(int(DELAY))

end = timer()
elapsed = end - start
print(f"\n\nprocessed {item_count - 1} items in {elapsed} seconds.")