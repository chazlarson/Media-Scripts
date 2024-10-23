from alive_progress import alive_bar, alive_it
from ruamel import yaml
from datetime import datetime, timedelta
import os
import platform
import re
from pathlib import Path
from plexapi.utils import download
from logs import setup_logger, plogger, blogger, logger
from helpers import (booler, get_all_from_library, get_ids, get_letter_dir, get_plex, has_overlay, get_size, redact, validate_filename, load_and_upgrade_env)

SCRIPT_NAME = Path(__file__).stem

# 0.0.3 : handle some errors better
# 0.0.4 : deal with invalid filenames
# 0.0.5 : file_poster not url_poster

VERSION = "0.0.5"

env_file_path = Path(".env")

# current dateTime
now = datetime.now()

IS_WINDOWS = platform.system() == "Windows"

# convert to string
RUNTIME_STR = now.strftime("%Y-%m-%d %H:%M:%S")

ACTIVITY_LOG = f"{SCRIPT_NAME}.log"

setup_logger('activity_log', ACTIVITY_LOG)

plogger(f"Starting {SCRIPT_NAME} {VERSION} at {RUNTIME_STR}", 'info', 'a')

if load_and_upgrade_env(env_file_path) < 0:
    exit()

LIBRARY_NAME = os.getenv("LIBRARY_NAME")
LIBRARY_NAMES = os.getenv("LIBRARY_NAMES")
# tmdb_key = os.getenv("TMDB_KEY")
# TVDB_KEY = os.getenv("TVDB_KEY")
# CAST_DEPTH = int(os.getenv("CAST_DEPTH"))
# TOP_COUNT = int(os.getenv("TOP_COUNT"))
DELAY = int(os.getenv("DELAY"))

if not DELAY:
    DELAY = 0

TARGET_URL_VAR = 'PLEX_URL'
plex_url = os.getenv(TARGET_URL_VAR)
if plex_url is None:
    TARGET_URL_VAR = 'PLEXAPI_AUTH_SERVER_BASEURL'
    plex_url = os.getenv(TARGET_URL_VAR)

if PLEX_URL.endswith('/'):
    plex_url = PLEX_URL[:-1]

TARGET_TOKEN_VAR = 'PLEX_TOKEN'
plex_token = os.getenv(TARGET_TOKEN_VAR)
if plex_token is None:
    TARGET_TOKEN_VAR = 'PLEXAPI_AUTH_SERVER_TOKEN'
    plex_token = os.getenv(TARGET_TOKEN_VAR)

if LIBRARY_NAMES:
    lib_array = LIBRARY_NAMES.split(",")
else:
    lib_array = [LIBRARY_NAME]

ARTWORK_DIR = "artwork"
BACKGROUND_DIR = "background"
CONFIG_DIR = "config"

plex = get_plex()

coll_obj = {}
coll_obj["collections"] = {}


def get_sort_text(argument):
    switcher = {0: "release", 1: "alpha", 2: "custom"}
    return switcher.get(argument, "invalid-sort")


for lib in lib_array:
    lib = lib.lstrip()
    safe_lib = re.sub(r"[/\\?%*:|\"<>\x7F\x00-\x1F]", "-", lib)
    print(f"Processing: [{lib}] | safe: [{safe_lib}]")
    try:
        the_lib = plex.library.section(lib)

        collections = the_lib.collections()
        item_total = len(collections)
        with alive_bar(item_total, dual_line=True, title=f"Extract collections: {the_lib.title}") as bar:
            for collection in collections:

                if collection.smart:
                    filters = collection.filters()

                title = collection.title

                safe_title = re.sub(r"[/\\?%*:|\"<>\x7F\x00-\x1F]", "-", title)

                print(f"title - {title} | safe - {safe_title}")

                artwork_path = Path(".", CONFIG_DIR, f"{safe_lib}-{ARTWORK_DIR}")
                artwork_path.mkdir(mode=511, parents=True, exist_ok=True)

                background_path = Path(".", CONFIG_DIR, f"{safe_lib}-{BACKGROUND_DIR}")
                background_path.mkdir(mode=511, parents=True, exist_ok=True)

                THUMBPATH = None
                ARTPATH = None

                try:
                    THUMBPATH = download(
                        f"{PLEX_URL}{collection.thumb}",
                        PLEX_TOKEN,
                        filename=f"{safe_title}.png",
                        savepath=artwork_path,
                    )
                except Exception as ex:
                    print(f"Continuing without image - {ex}")

                if collection.art is not None:
                    ARTPATH = download(
                        f"{PLEX_URL}{collection.art}",
                        PLEX_TOKEN,
                        filename=f"{safe_title}.png",
                        savepath=background_path,
                    )

                this_coll = {}
                this_coll["sort_title"] = collection.titleSort
                if THUMBPATH is not None:
                    this_coll["file_poster"] = f"./{THUMBPATH}"
                if ARTPATH is not None:
                    this_coll["file_background"] = f"./{ARTPATH}"

                if len(collection.summary) > 0:
                    this_coll["summary"] = collection.summary

                this_coll["collection_order"] = get_sort_text(collection.collectionSort)

                this_coll["plex_search"] = {}
                this_coll["plex_search"]["any"] = {}
                titlearray = []
                items = collection.items()
                for item in items:
                    titlearray.append(item.title)
                this_coll["plex_search"]["any"]["title.is"] = titlearray

                if len(this_coll) > 0:
                    coll_obj["collections"][collection.title] = this_coll

                bar()

        metadatafile_path = Path(".", CONFIG_DIR, f"{safe_lib}-existing.yml")


        if yaml.version_info < (0, 15):
            # data = yaml.load(istream, Loader=yaml.CSafeLoader)
            # yaml.round_trip_dump(data, ostream, width=1000, explicit_start=True)
            yaml.round_trip_dump(
                coll_obj,
                open(metadatafile_path, "w", encoding="utf-8"),
                indent=None,
                block_seq_indent=2,
            )
        else:
            # yml = ruamel.yaml.YAML(typ='safe')
            # data = yml.load(istream)
            if (len(coll_obj['collections']) > 0):
                ymlo = yaml.YAML()   # or yaml.YAML(typ='rt')
                ymlo.width = 1000
                ymlo.explicit_start = True
                ymlo.dump(coll_obj,
                    open(metadatafile_path, "w", encoding="utf-8"))
            else:
                print(f"{lib} has no collections to export")
    except Exception as ex:
        print(f"error loading library: {lib}")
        print(f"This server has: {plex.library.sections()}")

