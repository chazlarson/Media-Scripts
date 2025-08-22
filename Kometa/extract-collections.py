import platform
import re
from datetime import datetime
from pathlib import Path

from alive_progress import alive_bar
from config import Config
from helpers import get_plex, get_redaction_list, get_target_libraries
from logs import plogger, setup_logger
from plexapi.utils import download
from ruamel import yaml

SCRIPT_NAME = Path(__file__).stem

# 0.0.3 : handle some errors better
# 0.0.4 : deal with invalid filenames
# 0.0.5 : file_poster not url_poster

VERSION = "0.0.5"

# current dateTime
now = datetime.now()

IS_WINDOWS = platform.system() == "Windows"

# convert to string
RUNTIME_STR = now.strftime("%Y-%m-%d %H:%M:%S")

ACTIVITY_LOG = f"{SCRIPT_NAME}.log"

setup_logger("activity_log", ACTIVITY_LOG)

plogger(f"Starting {SCRIPT_NAME} {VERSION} at {RUNTIME_STR}", "info", "a")

config = Config('../config.yaml')

DELAY = config.get_int('general.delay', 0)

artwork_dir = "artwork"
background_dir = "background"
config_dir = "config"

PLEX_URL = config.get("plex_api.auth_server.base_url")
PLEX_TOKEN = config.get("plex_api.auth_server.token")

plex = get_plex()

LIB_ARRAY = get_target_libraries(plex)

coll_obj = {}
coll_obj["collections"] = {}


def get_sort_text(argument):
    switcher = {0: "release", 1: "alpha", 2: "custom"}
    return switcher.get(argument, "invalid-sort")


for lib in LIB_ARRAY:
    lib = lib.lstrip()
    safe_lib = re.sub(r"[/\\?%*:|\"<>\x7F\x00-\x1F]", "-", lib)
    print(f"Processing: [{lib}] | safe: [{safe_lib}]")
    try:
        the_lib = plex.library.section(lib)

        collections = the_lib.collections()
        item_total = len(collections)
        with alive_bar(
            item_total, dual_line=True, title=f"Extract collections: {the_lib.title}"
        ) as bar:
            for collection in collections:
                if collection.smart:
                    filters = collection.filters()

                title = collection.title

                safe_title = re.sub(r"[/\\?%*:|\"<>\x7F\x00-\x1F]", "-", title)

                print(f"title - {title} | safe - {safe_title}")

                artwork_path = Path(".", config_dir, f"{safe_lib}-{artwork_dir}")
                artwork_path.mkdir(mode=511, parents=True, exist_ok=True)

                background_path = Path(".", config_dir, f"{safe_lib}-{background_dir}")
                background_path.mkdir(mode=511, parents=True, exist_ok=True)

                thumbPath = None
                artPath = None

                try:
                    thumbPath = download(
                        f"{PLEX_URL}{collection.thumb}",
                        PLEX_TOKEN,
                        filename=f"{safe_title}.png",
                        savepath=artwork_path,
                    )
                except Exception as ex:
                    print(f"Continuing without image - {ex}")

                if collection.art is not None:
                    artPath = download(
                        f"{PLEX_URL}{collection.art}",
                        PLEX_TOKEN,
                        filename=f"{safe_title}.png",
                        savepath=background_path,
                    )

                this_coll = {}
                this_coll["sort_title"] = collection.titleSort
                if thumbPath is not None:
                    this_coll["file_poster"] = f"./{thumbPath}"
                if artPath is not None:
                    this_coll["file_background"] = f"./{artPath}"

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

        metadatafile_path = Path(".", config_dir, f"{safe_lib}-existing.yml")

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
            if len(coll_obj["collections"]) > 0:
                ymlo = yaml.YAML()  # or yaml.YAML(typ='rt')
                ymlo.width = 1000
                ymlo.explicit_start = True
                ymlo.dump(coll_obj, open(metadatafile_path, "w", encoding="utf-8"))
            else:
                print(f"{lib} has no collections to export")
    except Exception:
        print(f"error loading library: {lib}")
        print(f"This server has: {plex.library.sections()}")
