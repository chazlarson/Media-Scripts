from plexapi.server import PlexServer
import os
from dotenv import load_dotenv
import sys
import textwrap
import logging
import urllib3.exceptions
from urllib3.exceptions import ReadTimeoutError
from requests import ReadTimeout
from helpers import get_plex, get_all_from_library, load_and_upgrade_env
from alive_progress import alive_bar

import logging
from pathlib import Path
from datetime import datetime, timedelta
# current dateTime
now = datetime.now()

# convert to string
RUNTIME_STR = now.strftime("%Y-%m-%d %H:%M:%S")

SCRIPT_NAME = Path(__file__).stem

VERSION = "0.1.0"


env_file_path = Path(".env")

logging.basicConfig(
    filename=f"{SCRIPT_NAME}.log",
    filemode="w",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logging.info(f"Starting {SCRIPT_NAME}")
print(f"Starting {SCRIPT_NAME}")

status = load_and_upgrade_env(env_file_path)

LIBRARY_NAME = os.getenv("LIBRARY_NAME")
LIBRARY_NAMES = os.getenv("LIBRARY_NAMES")
UNMATCHED_ONLY = os.getenv("UNMATCHED_ONLY")

if LIBRARY_NAMES:
    LIB_ARRAY = LIBRARY_NAMES.split(",")
else:
    LIB_ARRAY = [LIBRARY_NAME]

tmdb_str = "tmdb://"
tvdb_str = "tvdb://"


def progress(count, total, status=""):
    bar_len = 40
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = "=" * filled_len + "-" * (bar_len - filled_len)
    stat_str = textwrap.shorten(status, width=80)

    sys.stdout.write("[%s] %s%s ... %s\r" % (bar, percents, "%", stat_str.ljust(80)))
    sys.stdout.flush()


plex = get_plex()

if LIBRARY_NAMES == 'ALL_LIBRARIES':
    LIB_ARRAY = []
    all_libs = plex.library.sections()
    for lib in all_libs:
        if lib.type == 'movie' or lib.type == 'show':
            LIB_ARRAY.append(lib.title.strip())

for lib in LIB_ARRAY:
    the_lib = plex.library.section(lib)
    print(f"getting items from [{lib}]...")
    logging.info(f"getting items from [{lib}]...")

    if UNMATCHED_ONLY:
        items = get_all_from_library(plex, the_lib, None, {'unmatched': True})
    else:
        items = get_all_from_library(plex, the_lib)

    item_total = len(items)
    print(f"looping over {item_total} items...")
    logging.info(f"looping over {item_total} items...")
    item_count = 0

    plex_links = []
    external_links = []

    if the_lib.type == 'movie':
        agents = [
            "com.plexapp.agents.imdb",
            "tv.plex.agents.movie",
            "com.plexapp.agents.themoviedb"
        ]
    elif the_lib.type == 'show':
        agents = [
            "com.plexapp.agents.thetvdb",
            "tv.plex.agents.series"
        ]
    else:
        agents = [
            "com.plexapp.agents.fanarttv",
            "com.plexapp.agents.none",
            "tv.plex.agents.music",
            "com.plexapp.agents.opensubtitles",
            "com.plexapp.agents.imdb",
            "com.plexapp.agents.lyricfind",
            "com.plexapp.agents.thetvdb",
            "tv.plex.agents.movie",
            "tv.plex.agents.series",
            "com.plexapp.agents.plexthememusic",
            "org.musicbrainz.agents.music",
            "com.plexapp.agents.themoviedb",
            "com.plexapp.agents.htbackdrops",
            "com.plexapp.agents.movieposterdb",
            "com.plexapp.agents.localmedia",
            "com.plexapp.agents.lastfm"
        ]


    with alive_bar(len(items), dual_line=True, title=f"Rematching") as bar:
        for item in items:
            tmpDict = {}
            item_count = item_count + 1
            matched_it = False

            for agt in agents:
                if not matched_it:
                    try:
                        progress_str = f"{item.title} - agent {agt}"
                        bar.text(progress_str)

                        progress(item_count, item_total, progress_str)

                        item.fixMatch(auto=True, agent=agt)

                        matched_it = True

                        progress_str = f"{item.title} - DONE"
                        progress(item_count, item_total, progress_str)

                    except urllib3.exceptions.ReadTimeoutError:
                        progress(item_count, item_total, "ReadTimeoutError: " + item.title)
                    except urllib3.exceptions.HTTPError:
                        progress(item_count, item_total, "HTTPError: " + item.title)
                    except ReadTimeoutError:
                        progress(item_count, item_total, "ReadTimeoutError-2: " + item.title)
                    except ReadTimeout:
                        progress(item_count, item_total, "ReadTimeout: " + item.title)
                    except Exception as ex:
                        progress(item_count, item_total, "EX: " + item.title)
                        logging.error(ex)
            bar()

