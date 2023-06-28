from plexapi.exceptions import Unauthorized
import logging
from alive_progress import alive_bar
from plexapi.server import PlexServer
from plexapi.exceptions import Unauthorized
import os
from dotenv import load_dotenv

from timeit import default_timer as timer
import time
from helpers import booler, get_all, get_plex
from pathlib import Path

start = timer()

import logging
from pathlib import Path
SCRIPT_NAME = Path(__file__).stem

logging.basicConfig(
    filename=f"{SCRIPT_NAME}.log",
    filemode="w",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

def bar_and_log(the_bar, msg):
    logging.info(msg)
    the_bar.text = msg

def print_and_log(msg):
    logging.info(msg)
    print(msg)


print_and_log(f"Starting {SCRIPT_NAME}")

if os.path.exists(".env"):
    load_dotenv()
else:
    print_and_log(f"No environment [.env] file.  Exiting.")
    exit()

PLEX_URL = os.getenv("PLEX_URL")

if PLEX_URL is None:
    print_and_log("Your .env file is incomplete or missing: PLEX_URL is empty")
    exit()

PLEX_TOKEN = os.getenv("PLEX_TOKEN")
LIBRARY_NAME = os.getenv("LIBRARY_NAME")
LIBRARY_NAMES = os.getenv("LIBRARY_NAMES")
TARGET_LABELS = os.getenv("TARGET_LABELS")
TRACK_RESET_STATUS = os.getenv("TRACK_RESET_STATUS")
REMOVE_LABELS = booler(os.getenv("REMOVE_LABELS"))
RESET_SEASONS = booler(os.getenv("RESET_SEASONS"))
RESET_EPISODES = booler(os.getenv("RESET_EPISODES"))

DELAY = 0
try:
    DELAY = int(os.getenv("DELAY"))
except:
    DELAY = 0

if TARGET_LABELS:
    LBL_ARRAY = TARGET_LABELS.split(",")
else:
    LBL_ARRAY = ["xy22y1973"]

if LIBRARY_NAMES:
    LIB_ARRAY = LIBRARY_NAMES.split(",")
else:
    LIB_ARRAY = [LIBRARY_NAME]

plex = get_plex(PLEX_URL, PLEX_TOKEN)
print_and_log("connection success")

if LIBRARY_NAMES == 'ALL_LIBRARIES':
    LIB_ARRAY = []
    all_libs = plex.library.sections()
    for lib in all_libs:
        if lib.type == 'movie' or lib.type == 'show':
            LIB_ARRAY.append(lib.title.strip())

for lib in LIB_ARRAY:
    id_array = []
    the_lib = plex.library.section(lib)
    the_type = the_lib.type
    status_file_name = the_lib.uuid + ".txt"
    status_file = Path(status_file_name)

    if status_file.is_file():
        with open(f"{status_file_name}") as fp:
            for line in fp:
                id_array.append(line.strip())

    for lbl in LBL_ARRAY:
        if lbl == "xy22y1973":
            print_and_log(f"{os.linesep}getting all items from the {the_type} library [{lib}]...")
            items = get_all(plex, the_lib)
            REMOVE_LABELS = False
        else:
            print_and_log(
                f"{os.linesep}getting items from the {the_type} library [{lib}] with the label [{lbl}]..."
            )
            items = the_lib.search(label=lbl)
        item_total = len(items)
        print_and_log(f"{item_total} item(s) retrieved...")
        item_count = 1
        with alive_bar(item_total, dual_line=True, title="Poster Reset - Plex") as bar:
            for item in items:
                item_count = item_count + 1
                if id_array.count(f"{item.ratingKey}") == 0:
                    id_array.append(item.ratingKey)

                    try:
                        bar_and_log(bar, f"-> starting: {item.title}")
                        pp = None
                        local_file = None

                        bar_and_log(bar, f"-> getting posters: {item.title}")
                        posters = item.posters()
                        bar_and_log(bar, f"-> setting poster: {item.title}")
 
                        if len(posters) > 0:
                            showPoster = posters[0]
                            bar_and_log(bar, f"-> setting {the_type} poster for {item.title} to {showPoster.thumb}")
                            item.setPoster(showPoster)
                        else:
                            showPoster = None

                        if REMOVE_LABELS:
                            bar_and_log(bar, f"-> removing label {lbl}: {item.title}")
                            item.removeLabel(lbl, True)

                        # write out item_array to file.
                        with open(status_file, "a", encoding="utf-8") as sf:
                            sf.write(f"{item.ratingKey}{os.linesep}")

                        if item.TYPE == "show":
                            if RESET_SEASONS:
                                # get seasons
                                seasons = item.seasons()
                                # loop over all:
                                for s in seasons:
                                    # reset artwork
                                    bar_and_log(bar, 
                                        f"-> getting season posters: {s.parentTitle}-{s.seasonNumber}-{s.title}"
                                    )
                                    posters = s.posters()
                                    if len(posters) > 0:
                                        seasonPoster = posters[0]
                                    else:
                                        seasonPoster = showPoster

                                    if seasonPoster is not None:
                                        bar_and_log(bar, 
                                            f"-> setting season poster for : {s.parentTitle}-{s.seasonNumber}-{s.title} to {seasonPoster.thumb}"
               	                        )
                                        s.setPoster(seasonPoster)

                                    if RESET_EPISODES:
                                        # get episodes
                                        episodes = s.episodes()
                                        # loop over all
                                        for e in episodes:
                                            # reset artwork
                                            # reset artwork
                                            bar_and_log(bar, f"-> getting episode posters: {s.parentTitle}-{s.seasonNumber}-{s.title}-{e.episodeNumber}-{e.title}")
                                            posters = e.posters()
                                            if len(posters) > 0:
                                                episodePoster = posters[0]
                                            else:
                                                episodePoster = showPoster

                                            if episodePoster is not None:
                                                bar_and_log(bar, f"-> setting episode poster: {s.parentTitle}-{s.title}-{e.episodeNumber}-{e.title} to {episodePoster.thumb}")
                                                s.setPoster(episodePoster)

                    except Exception as ex:
                        print_and_log(f'Exception processing "{item.title}": {ex}')

                    bar()

                    # Wait between items in case hammering the Plex server turns out badly.
                    time.sleep(DELAY)

    # delete the status file
    if status_file.is_file():
        os.remove(status_file)

end = timer()
elapsed = end - start
print_and_log(f"{os.linesep}{os.linesep}processed {item_count - 1} items in {elapsed} seconds.")
