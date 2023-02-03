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

logging.info(f"Starting {SCRIPT_NAME}")
print(f"Starting {SCRIPT_NAME}")

if os.path.exists(".env"):
    load_dotenv()
else:
    logging.info(f"No environment [.env] file.  Exiting.")
    print(f"No environment [.env] file.  Exiting.")
    exit()

PLEX_URL = os.getenv("PLEX_URL")

if PLEX_URL is None:
    print("Your .env file is incomplete or missing: PLEX_URL is empty")
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
logging.info("connection success")

if LIBRARY_NAMES == 'ALL_LIBRARIES':
    LIB_ARRAY = []
    all_libs = plex.library.sections()
    for lib in all_libs:
        if lib.type == 'movie' or lib.type == 'show':
            LIB_ARRAY.append(lib.title.strip())

for lib in LIB_ARRAY:
    id_array = []
    the_lib = plex.library.section(lib)
    status_file_name = the_lib.uuid + ".txt"
    status_file = Path(status_file_name)

    if status_file.is_file():
        with open(f"{status_file_name}") as fp:
            for line in fp:
                id_array.append(line.strip())

    for lbl in LBL_ARRAY:
        if lbl == "xy22y1973":
            print(f"{os.linesep}getting all items from the library [{lib}]...")
            items = get_all(plex, the_lib)
            REMOVE_LABELS = False
        else:
            print(
                f"{os.linesep}getting items from the library [{lib}] with the label [{lbl}]..."
            )
            items = the_lib.search(label=lbl)
        item_total = len(items)
        print(f"{item_total} item(s) retrieved...")
        item_count = 1
        with alive_bar(item_total, dual_line=True, title="Poster Reset - Plex") as bar:
            for item in items:
                item_count = item_count + 1
                if id_array.count(f"{item.ratingKey}") == 0:
                    id_array.append(item.ratingKey)

                    try:
                        bar.text = f"-> starting: {item.title}"
                        pp = None
                        local_file = None

                        bar.text = f"-> getting posters: {item.title}"
                        posters = item.posters()
                        bar.text = f"-> setting poster: {item.title}"
 
                        if len(posters) > 0:
                           showPoster = posters[0]
                           item.setPoster(showPoster)
                        else:
                           showPoster = None

                        if REMOVE_LABELS:
                            bar.text = f"-> removing label {lbl}: {item.title}"
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
                                    bar.text = (
                                        f"-> getting posters: {s.parentTitle}-{s.title}"
                                    )
                                    posters = s.posters()
                                    if len(posters) > 0:
                                        seasonPoster = posters[0]
                                    else:
                                        seasonPoster = showPoster

                                    if seasonPoster is not None:
                                        bar.text = (
                                            f"-> setting poster: {s.parentTitle}-{s.title}"
               	                        )
                                        s.setPoster(seasonPoster)

                                    if RESET_EPISODES:
                                        # get episodes
                                        episodes = s.episodes()
                                        # loop over all
                                        for e in episodes:
                                            # reset artwork
                                            # reset artwork
                                            bar.text = f"-> getting posters: {s.parentTitle}-{s.title}-{e.episodeNumber}-{e.title}"
                                            posters = e.posters()
                                            if len(posters) > 0:
                                                episodePoster = posters[0]
                                            else:
                                                episodePoster = showPoster

                                            if episodePoster is not None:
                                                bar.text = f"-> setting poster: {s.parentTitle}-{s.title}-{e.episodeNumber}-{e.title}"
                                                s.setPoster(episodePoster)

                    except Exception as ex:
                        print(f'Exception processing "{item.title}": {ex}')

                    bar()

                    # Wait between items in case hammering the Plex server turns out badly.
                    time.sleep(DELAY)

    # delete the status file
    if status_file.is_file():
        os.remove(status_file)

end = timer()
elapsed = end - start
print(f"{os.linesep}{os.linesep}processed {item_count - 1} items in {elapsed} seconds.")
