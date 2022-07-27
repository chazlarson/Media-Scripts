import tmdbsimple as tmdb
import requests
from dotenv import load_dotenv
from alive_progress import alive_bar
from plexapi.server import PlexServer
import os
import sys
import textwrap
from tmdbapis import TMDbAPIs
import requests
import pathlib
from pathlib import Path
import platform
from timeit import default_timer as timer
import time

start = timer()

load_dotenv()

TMDB_KEY = os.getenv('TMDB_KEY')
POSTER_DIR = os.getenv('POSTER_DIR')
PERSON_DEPTH = 0
try:
    PERSON_DEPTH = int(os.getenv('PERSON_DEPTH'))
except:
    PERSON_DEPTH = 0


tmdb.API_KEY = TMDB_KEY
tmdb.REQUESTS_SESSION = requests.Session()
image_path = POSTER_DIR
actor_name_file = 'actor_names.txt'

items = []

actor_file = Path(actor_name_file)

if actor_file.is_file():
    with open(f"{actor_name_file}") as fp:
        for line in fp:
            items.append(line.strip())

search = tmdb.Search()
idx = 1

item_total = len(items)
print(f"{item_total} item(s) retrieved...")
item_count = 1
with alive_bar(item_total, dual_line=True, title='TMDB people') as bar:
    for item in items:
        bar.text = f'-> starting: {item}'
        item_count = item_count + 1

        response = search.person(query=item)
        idx = 0
        UPPER = PERSON_DEPTH

        if len(search.results) < PERSON_DEPTH:
            UPPER = len(search.results)

        for i in range(0,UPPER):
            try:
                s = search.results[i]

                idx = idx + 1

                bar.text = f"-> retrieving: {idx}-{s['id']}-{s['name']}"
                url = f"https://www.themoviedb.org/t/p/w600_and_h900_bestv2{s['profile_path']}"

                r = requests.get(url)

                filepath = Path(f"{image_path}/{s['id']}-{s['name']}.jpg")
                filepath.parent.mkdir(parents=True, exist_ok=True)

                with filepath.open("wb") as f:
                    f.write(r.content)
            except:
                bar.text = f'-> exception: {item}'


        bar()
