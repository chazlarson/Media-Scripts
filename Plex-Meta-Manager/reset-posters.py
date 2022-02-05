from collections import Counter
from typing import Collection
from plexapi.server import PlexServer
import os
from dotenv import load_dotenv
import sys
import textwrap
from tmdbv3api import TMDb
from tmdbv3api import Movie
from tmdbv3api import TV
from tmdbv3api import Configuration
import requests
import pathlib
# import tvdb_v4_official

load_dotenv()

PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')
LIBRARY_NAME = os.getenv('LIBRARY_NAME')
TMDB_KEY = os.getenv('TMDB_KEY')
TVDB_KEY = os.getenv('TVDB_KEY')
CAST_DEPTH = int(os.getenv('CAST_DEPTH'))
TOP_COUNT = int(os.getenv('TOP_COUNT'))

# Commented out until this doesn't throw a 400
# tvdb = tvdb_v4_official.TVDB(TVDB_KEY)

tmdb = TMDb()
tmdb.api_key = TMDB_KEY

tmdbMovie = Movie()
tmdbTV = TV()
tmdbConfig = Configuration()

tmdb_str = 'tmdb://'

local_dir = f"{os.getcwd()}/posters"

os.makedirs(local_dir, exist_ok=True)

show_dir = f"{local_dir}/shows"
movie_dir = f"{local_dir}/movies"

os.makedirs(show_dir, exist_ok=True)
os.makedirs(movie_dir, exist_ok=True)

def getTMDBID(theList):
    for guid in theList:
        if tmdb_str in guid.id:
            return guid.id.replace(tmdb_str,'')
    return None

def progress(count, total, status=''):
    bar_len = 40
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)
    stat_str = textwrap.shorten(status, width=30)

    sys.stdout.write('[%s] %s%s ... %s\r' % (bar, percents, '%', stat_str.ljust(30)))
    sys.stdout.flush()

print("tmdb config...")
tmdbInfo = tmdbConfig.info()
base_url = tmdbInfo.images.secure_base_url
size_str = 'original'

print(f"connecting to {PLEX_URL}...")
plex = PlexServer(PLEX_URL, PLEX_TOKEN)
print(f"getting items from [{LIBRARY_NAME}]...")
items = plex.library.section(LIBRARY_NAME).all()
item_total = len(items)
print(f"looping over {item_total} items...")
item_count = 1
for item in items:
    tmpDict = {}
    theID = getTMDBID(item.guids)
    item_count = item_count + 1
    try:
        progress(item_count, item_total, item.title)
        pp = None
        if item.TYPE == 'show':
            pp = tmdbTV.details(theID).poster_path
            tgt_dir = show_dir
        else:
            pp = tmdbMovie.details(theID).poster_path
            tgt_dir = movie_dir

        if pp is not None:
            ext = pathlib.Path(pp).suffix
            posterURL = f"{base_url}{size_str}{pp}"
            local_file = f"{tgt_dir}/{item.ratingKey}{ext}"
            if not os.path.exists(local_file):
                r = requests.get(posterURL, allow_redirects=True)
                open(f"{local_file}", 'wb').write(r.content)
            item.uploadPoster(filepath=local_file)
        else:
            progress(item_count, item_total, "unknown type: " + item.title)

    except Exception as ex:
        progress(item_count, item_total, "EX: " + item.title)
