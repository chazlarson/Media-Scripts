from collections import Counter
from typing import Collection
from plexapi.server import PlexServer
import os
from dotenv import load_dotenv
import sys
import textwrap
from tmdbv3api import TMDb
from tmdbv3api import Movie

load_dotenv()

PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')
MOVIE_LIBRARY_NAME = os.getenv('MOVIE_LIBRARY_NAME')
TMDB_KEY = os.getenv('TMDB_KEY')
CAST_DEPTH = int(os.getenv('CAST_DEPTH'))
TOP_COUNT = int(os.getenv('TOP_COUNT'))

tmdb = TMDb()
tmdb.api_key = TMDB_KEY

tmdbMovie = Movie()

tmdb_str = 'tmdb://'

METADATA_TITLE = f"{MOVIE_LIBRARY_NAME} Top {TOP_COUNT} Actors.yml"

actors = Counter()

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

print("connecting...")
plex = PlexServer(PLEX_URL, PLEX_TOKEN)
print("getting movies...")
movies = plex.library.section(MOVIE_LIBRARY_NAME).all()
movie_total = len(movies)
print(f"looping over {movie_total} movies...")
movie_count = 1
for movie in movies:
    tmpDict = {}
    theID = getTMDBID(movie.guids)
    movie_count = movie_count + 1
    try:
        progress(movie_count, movie_total, movie.title)
        cast = tmdbMovie.details(theID).casts['cast']
        count = 0
        for actor in cast:
            if count < CAST_DEPTH:
                count = count + 1
                if actor['known_for_department'] == 'Acting':
                    tmpDict[f"{actor['id']}-{actor['name']}"] = 1
        actors.update(tmpDict)
    except Exception as ex:
        progress(movie_count, movie_total, "EX: " + movie.title)


print("\r\r")
YAML_STR = ''
COLL_TMPL = ''

with open('template.tmpl') as tmpl:
    YAML_STR = tmpl.read()

with open('collection.tmpl') as tmpl:
    COLL_TMPL = tmpl.read()

count = 0
for actor in sorted(actors.items(), key=lambda x: x[1], reverse=True):
    if count < TOP_COUNT:
        print("{}\t{}".format(actor[1], actor[0]))
        name_arr = actor[0].split('-')
        this_coll = COLL_TMPL.replace("%%NAME%%", name_arr[1])
        this_coll = this_coll.replace("%%ID%%", name_arr[0])
        YAML_STR = YAML_STR + this_coll
        count = count + 1

with open(METADATA_TITLE, "w") as out:
    out.write(YAML_STR)

