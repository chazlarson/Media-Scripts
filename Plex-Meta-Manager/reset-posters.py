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

def boolean_string(s):
    if s not in {'False', 'True'}:
        raise ValueError('Not a valid boolean string')
    return s == 'True'

PLEX_URL = os.getenv('PLEX_URL')

if PLEX_URL is None:
    print("Your .env file is incomplete or missing: PLEX_URL is empty")
    exit()

PLEX_TOKEN = os.getenv('PLEX_TOKEN')
LIBRARY_NAME = os.getenv('LIBRARY_NAME')
LIBRARY_NAMES = os.getenv('LIBRARY_NAMES')
TMDB_KEY = os.getenv('TMDB_KEY')
TVDB_KEY = os.getenv('TVDB_KEY')
TARGET_LABELS = os.getenv('TARGET_LABELS')
REMOVE_LABELS = boolean_string(os.getenv('REMOVE_LABELS'))
print(f"os.getenv('REMOVE_LABELS'): {os.getenv('REMOVE_LABELS')}")
print(f"REMOVE_LABELS: {REMOVE_LABELS}")
DELAY = 0
try:
    DELAY = int(os.getenv('DELAY'))
except:
    DELAY = 0

if TARGET_LABELS:
    lbl_array = TARGET_LABELS.split(",")
else:
    lbl_array = ["xy22y1973"]

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

def localFilePath(tgt_dir, rating_key):
    for ext in ['jpg','png']:
        local_file = f"{tgt_dir}/{item.ratingKey}.{ext}"
        if os.path.exists(local_file):
            return local_file
    return None

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
    stat_str = textwrap.shorten(status, width=60)

    sys.stdout.write('[%s] %s%s ... %s\r' % (bar, percents, '%', stat_str.ljust(60)))
    sys.stdout.flush()

print("tmdb config...")

base_url = tmdb.configuration().secure_base_image_url
size_str = 'original'

print(f"connecting to {PLEX_URL}...")
plex = PlexServer(PLEX_URL, PLEX_TOKEN)
for lib in lib_array:
    print(f"\ngetting items from [{lib}]...")
    for lbl in lbl_array:
        if lbl == "xy22y1973":
            items = plex.library.section(lib).all()
            REMOVE_LABELS = False
        else:
            print(f"\nlabelled [{lbl}]...")
            items = plex.library.section(lib).search(label=lbl)
        item_total = len(items)
        print(f"looping over {item_total} items...")
        item_count = 1
        for item in items:
            tmdb_id, tvdb_id = getTID(item.guids)
            item_count = item_count + 1
            try:
                progress(item_count, item_total, item.title)
                pp = None
                local_file = None

                if item.TYPE == 'show':
                    tgt_dir = show_dir
                    local_file = localFilePath(tgt_dir, item.ratingKey)
                    pp = local_file
                    if local_file is None:
                        try:
                            pp = tmdb.tv_show(tmdb_id).poster_path if tmdb_id else tmdb.find_by_id(tvdb_id=tvdb_id).tv_results[0].poster_path
                        except:
                            pp = "NONE"
                else:
                    tgt_dir = movie_dir
                    local_file = localFilePath(tgt_dir, item.ratingKey)
                    pp = local_file
                    if local_file is None:
                        try:
                            pp = tmdb.movie(tmdb_id).poster_path
                        except:
                            pp = "NONE"

                if pp is not None:
                    if pp == "NONE":
                        progress(item_count, item_total, item.title + " - getting posters")
                        posters = item.posters()
                        progress(item_count, item_total, item.title + " - setting poster")
                        item.setPoster(posters[0])
                    else:
                        if not os.path.exists(local_file):
                            ext = pathlib.Path(pp).suffix
                            posterURL = f"{base_url}{size_str}{pp}"
                            local_file = f"{tgt_dir}/{item.ratingKey}.{ext}"
                            progress(item_count, item_total, item.title + " - downloading poster")

                        if not os.path.exists(local_file):
                            r = requests.get(posterURL, allow_redirects=True)
                            open(f"{local_file}", 'wb').write(r.content)
                        progress(item_count, item_total, item.title + " - uploading poster")
                        item.uploadPoster(filepath=local_file)
                else:
                    progress(item_count, item_total, "unknown type: " + item.title)

                if REMOVE_LABELS:
                    progress(item_count, item_total, item.title + " - removing label")
                    item.removeLabel(lbl, True)

            except Exception as ex:
                progress(item_count, item_total, "EX: " + item.title)

            # Wait between items in case hammering the Plex server turns out badly.
            time.sleep(DELAY)

end = timer()
elapsed = end - start
print(f"\n\nprocessed {item_count - 1} items in {elapsed} seconds.")
