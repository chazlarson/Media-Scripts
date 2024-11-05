""" Rematch items in a Plex library """
#!/usr/bin/env python
import os
import sys
import textwrap
import logging
from pathlib import Path
from datetime import datetime
import urllib3.exceptions
from requests import ReadTimeout
from helpers import booler, get_plex, get_all_from_library, load_and_upgrade_env
from alive_progress import alive_bar

from logs import setup_logger, plogger
# current dateTime
now = datetime.now()

# convert to string
RUNTIME_STR = now.strftime("%Y-%m-%d %H:%M:%S")

SCRIPT_NAME = Path(__file__).stem

# DONE 0.2.0: chattier about where we're getting items
# DONE 0.2.1: Use booler helper to ensure correct var reading

VERSION = "0.2.1"

env_file_path = Path(".env")

ACTIVITY_LOG = f"{SCRIPT_NAME}.log"
setup_logger('activity_log', ACTIVITY_LOG)

plogger(f"Starting {SCRIPT_NAME} {VERSION} at {RUNTIME_STR}", 'info', 'a')

if load_and_upgrade_env(env_file_path) < 0:
    sys.exit()

LIBRARY_NAME = os.getenv("LIBRARY_NAME")
LIBRARY_NAMES = os.getenv("LIBRARY_NAMES")
UNMATCHED_ONLY = booler(os.getenv("UNMATCHED_ONLY"))

if LIBRARY_NAMES:
    LIB_ARRAY = LIBRARY_NAMES.split(",")
else:
    LIB_ARRAY = [LIBRARY_NAME]

TMDB_STR = "tmdb://"
TVDB_STR = "tvdb://"


def progress(count, total, status=""):
    """ Progress bar """
    bar_len = 40
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    p_bar = "=" * filled_len + "-" * (bar_len - filled_len)
    stat_str = textwrap.shorten(status, width=80)

    sys.stdout.write(f"[{p_bar}] {percents}% ... {stat_str.ljust(80)}\r")
    sys.stdout.flush()


plex = get_plex()

if LIBRARY_NAMES == 'ALL_LIBRARIES':
    LIB_ARRAY = []
    all_libs = plex.library.sections()
    for lib in all_libs:
        if lib.type in ('movie', 'show'):
            LIB_ARRAY.append(lib.title.strip())

for lib in LIB_ARRAY:
    the_lib = plex.library.section(lib)
    plogger(f"getting items from [{lib}]...", 'info', 'a')

    if UNMATCHED_ONLY:
        print(f"getting UNMATCHED items from [{lib}]...")
        item_total, items = get_all_from_library(the_lib, None, {'unmatched': True})
    else:
        item_total, items = get_all_from_library(the_lib)

    plogger(f"looping over {item_total} items...", 'info', 'a')
    ITEM_COUNT = 0

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


    with alive_bar(len(items), dual_line=True, title="Rematching") as bar:
        for item in items:
            tmpDict = {}
            ITEM_COUNT = ITEM_COUNT + 1
            MATCHED_IT = False

            for agt in agents:
                if not MATCHED_IT:
                    try:
                        bar.text(f"{item.title} - agent {agt}")

                        item.fixMatch(auto=True, agent=agt)

                        MATCHED_IT = True

                        bar.text(f"{item.title} - DONE")

                    except urllib3.exceptions.ReadTimeoutError:
                        progress(ITEM_COUNT, item_total, "ReadTimeoutError: " + item.title)
                    except urllib3.exceptions.HTTPError:
                        progress(ITEM_COUNT, item_total, "HTTPError: " + item.title)
                    except ReadTimeout:
                        progress(ITEM_COUNT, item_total, "ReadTimeout: " + item.title)
                    except Exception as ex: # pylint: disable=broad-exception-caught
                        progress(ITEM_COUNT, item_total, "EX: " + item.title)
                        logging.error(ex)
            bar() # pylint: disable=not-callable
