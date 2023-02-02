import logging
import os
from multiprocessing import cpu_count
from multiprocessing.pool import ThreadPool

import piexif.helper
from alive_progress import alive_bar
from dotenv import load_dotenv

from helpers import booler, get_all, get_plex

logging.basicConfig(
    filename="reverse-genres.log",
    filemode="w",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logging.info("Starting reverse-genres.py")

if os.path.exists(".env"):
    load_dotenv()
else:
    logging.info(f"No environment [.env] file.  Exiting.")
    print(f"No environment [.env] file.  Exiting.")
    exit()

PLEX_URL = os.getenv("PLEX_URL")
PLEX_TOKEN = os.getenv("PLEX_TOKEN")
LIBRARY_NAME = os.getenv("LIBRARY_NAME")
LIBRARY_NAMES = os.getenv("LIBRARY_NAMES")
NEW = []
UPDATED = []

if LIBRARY_NAMES:
    LIB_ARRAY = [s.strip() for s in LIBRARY_NAMES.split(",")]
else:
    LIB_ARRAY = [LIBRARY_NAME]

plex = get_plex(PLEX_URL, PLEX_TOKEN)

logging.info("connection success")

def reverse_genres(item):
    reversed_list = []

    item.reload()
    genres = item.genres

    print(f"{item.title} before: {genres}")

    item.removeGenre(genres)

    for genre in genres:
        reversed_list.insert(0, genre)
    
    print(f"{item.title} reversed: {reversed_list}")

    for genre in reversed_list:
        print(f"{item.title} adding: {genre}")
        item.addGenre(genre)
        item.reload()

    item.reload()
    new_genres = item.genres

    print(f"{item.title} after: {new_genres}")


if LIBRARY_NAMES == 'ALL_LIBRARIES':
    LIB_ARRAY = []
    all_libs = plex.library.sections()
    for lib in all_libs:
        if lib.type == 'movie' or lib.type == 'show':
            LIB_ARRAY.append(lib.title.strip())

for lib in LIB_ARRAY:

    try:
        the_lib = plex.library.section(lib)

        count = plex.library.section(lib).totalSize
        print(f"getting {count} {the_lib.type}s from [{lib}]...")
        logging.info(f"getting {count} {the_lib.type}s from [{lib}]...")
        items = get_all(plex, the_lib)
        # items = the_lib.all()
        item_total = len(items)
        logging.info(f"looping over {item_total} items...")
        item_count = 1

        plex_links = []
        external_links = []

        with alive_bar(item_total, dual_line=True, title="Reverse Genres") as bar:
            for item in items:
                logging.info("================================")
                logging.info(f"Starting {item.title}")

                reverse_genres(item)

                bar()

        progress_str = "COMPLETE"
        logging.info(progress_str)

        bar.text = progress_str

        print(os.linesep)

    except Exception as ex:
        progress_str = f"Problem processing {lib}; {ex}"
        logging.info(progress_str)

        print(progress_str)
