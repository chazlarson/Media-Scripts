from alive_progress import alive_bar
from plexapi.server import PlexServer
import os
from dotenv import load_dotenv
import sys
import textwrap
from tmdbapis import TMDbAPIs
import requests
import pathlib
import platform
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
TRACK_RESET_STATUS = os.getenv('TRACK_RESET_STATUS')
REMOVE_LABELS = boolean_string(os.getenv('REMOVE_LABELS'))
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

IS_WINDOWS = platform.system() == 'Windows'

# Commented out until this doesn't throw a 400
# tvdb = tvdb_v4_official.TVDB(TVDB_KEY)

tmdb = TMDbAPIs(TMDB_KEY, language="en")

tmdb_str = 'tmdb://'
tvdb_str = 'tvdb://'

local_dir = os.path.join(os.getcwd(), "posters")

os.makedirs(local_dir, exist_ok=True)

show_dir = os.path.join(os.getcwd(), "shows")
movie_dir = os.path.join(os.getcwd(), "movies")

os.makedirs(show_dir, exist_ok=True)
os.makedirs(movie_dir, exist_ok=True)

def localFilePath(tgt_dir, rating_key):
    for ext in ['jpg','png']:
        local_file = os.path.join(tgt_dir, f"{item.ratingKey}.{ext}")
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

print("tmdb config...")

base_url = tmdb.configuration().secure_base_image_url
size_str = 'original'

from pathlib import Path

print(f"connecting to {PLEX_URL}...")
plex = PlexServer(PLEX_URL, PLEX_TOKEN)
for lib in lib_array:
    id_array = []
    status_file_name = plex.library.section(lib).uuid + ".txt"
    status_file = Path(status_file_name)

    if status_file.is_file():
        with open(f"{status_file_name}") as fp:
            for line in fp:
                id_array.append(line.strip())

    for lbl in lbl_array:
        if lbl == "xy22y1973":
            print(f"{os.linesep}getting all items from the library [{lib}]...")
            items = plex.library.section(lib).all()
            REMOVE_LABELS = False
        else:
            print(f"{os.linesep}getting items from the library [{lib}] with the label [{lbl}]...")
            items = plex.library.section(lib).search(label=lbl)
        item_total = len(items)
        print(f"{item_total} item(s) retrieved...")
        item_count = 1
        with alive_bar(item_total, dual_line=True, title='Poster Reset - TMDB') as bar:
            for item in items:
                item_count = item_count + 1
                if id_array.count(f"{item.ratingKey}") == 0:
                    id_array.append(item.ratingKey)

                    tmdb_id, tvdb_id = getTID(item.guids)
                    try:
                        bar.text = f'-> starting: {item.title}'
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
                                bar.text = f'-> getting posters: {item.title}'
                                posters = item.posters()
                                bar.text = f'-> setting poster: {item.title}'
                                item.setPoster(posters[0])
                            else:
                                if local_file is None or not os.path.exists(local_file):
                                    ext = pathlib.Path(pp).suffix
                                    posterURL = f"{base_url}{size_str}{pp}"
                                    local_file = os.path.join(tgt_dir, f"{item.ratingKey}.{ext}")
                                    bar.text = f'-> downloading poster: {item.title}'

                                if not os.path.exists(local_file):
                                    r = requests.get(posterURL, allow_redirects=True)
                                    open(f"{local_file}", 'wb').write(r.content)
                                bar.text = f'-> uploading poster: {item.title}'
                                item.uploadPoster(filepath=local_file)
                        else:
                            bar.text = f'-> unknown type: {item.title}'

                        if REMOVE_LABELS:
                            bar.text = f'-> removing label {lbl}: {item.title}'
                            item.removeLabel(lbl, True)

                        # write out item_array to file.
                        with open(status_file, "a") as sf:
                            sf.write(f"{item.ratingKey}{os.linesep}")

                    except Exception as ex:
                        print(f'Exception processing "{item.title}"')

                    bar()

                    # Wait between items in case hammering the Plex server turns out badly.
                    time.sleep(DELAY)

    # delete the status file
    if status_file.is_file():
        os.remove(status_file)

end = timer()
elapsed = end - start
print(f"{os.linesep}{os.linesep}processed {item_count - 1} items in {elapsed} seconds.")
