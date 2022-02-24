from plexapi.server import PlexServer
from plexapi.utils import download
from ruamel import yaml
import os
from pathlib import Path, PurePath
from dotenv import load_dotenv

load_dotenv()

PLEX_URL = os.getenv('PLEX_URL')
PLEX_TOKEN = os.getenv('PLEX_TOKEN')
LIBRARY_NAME = os.getenv('LIBRARY_NAME')
LIBRARY_NAMES = os.getenv('LIBRARY_NAMES')
TMDB_KEY = os.getenv('TMDB_KEY')
TVDB_KEY = os.getenv('TVDB_KEY')
CAST_DEPTH = int(os.getenv('CAST_DEPTH'))
TOP_COUNT = int(os.getenv('TOP_COUNT'))
DELAY = int(os.getenv('DELAY'))

if not DELAY:
    DELAY = 0

if LIBRARY_NAMES:
    lib_array = LIBRARY_NAMES.split(",")
else:
    lib_array = [LIBRARY_NAME]

artwork_dir = "artwork"
background_dir = "background"
config_dir = 'config'

plex = PlexServer(PLEX_URL, PLEX_TOKEN)

coll_obj = {}
coll_obj['collections'] = {}

def get_sort_text(argument):
    switcher = {
        0: "release",
        1: "alpha",
        2: "custom"
    }
    return switcher.get(argument, "invalid-sort")

for lib in lib_array:
    movies = plex.library.section(lib)
    collections = movies.collections()
    for collection in collections:

        title = collection.title

        print(f"title - {title}")

        artwork_path = Path('.', config_dir, f"{lib}-{artwork_dir}")
        artwork_path.mkdir(mode=511, parents=True, exist_ok=True)

        background_path = Path('.', config_dir, f"{lib}-{background_dir}")
        background_path.mkdir(mode=511, parents=True, exist_ok=True)

        thumbPath = download(f"{PLEX_URL}{collection.thumb}", PLEX_TOKEN, filename=f"{collection.title}.png", savepath=artwork_path)

        if collection.art is not None:
            artPath = download(f"{PLEX_URL}{collection.art}", PLEX_TOKEN, filename=f"{collection.title}.png", savepath=background_path)
        else:
            artPath = None

        this_coll = {}
        this_coll["sort_title"] = collection.titleSort
        this_coll["url_poster"] = f"./{thumbPath}"
        if artPath is not None:
            this_coll["url_background"] = f"./{artPath}"

        if len(collection.summary) > 0:
            this_coll["summary"] = collection.summary

        this_coll["collection_order"] = get_sort_text(collection.collectionSort)

        this_coll["plex_search"] = {}
        this_coll["plex_search"]["any"] = {}
        titlearray = []
        items = collection.items()
        for item in items:
            titlearray.append(item.title)
        this_coll["plex_search"]["any"]["title"] = titlearray

        if len(this_coll) > 0:
            coll_obj['collections'][collection.title] = this_coll

    metadatafile_path = Path('.', config_dir, f"{lib}-existing.yml")

    yaml.round_trip_dump(coll_obj, open(metadatafile_path, "w", encoding="utf-8"), indent=None, block_seq_indent=2)
