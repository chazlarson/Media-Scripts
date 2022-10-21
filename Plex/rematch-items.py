from plexapi.server import PlexServer
import os
from dotenv import load_dotenv
import sys
import textwrap
import logging
import urllib3.exceptions
from urllib3.exceptions import ReadTimeoutError
from requests import ReadTimeout

load_dotenv()

logging.basicConfig(
    filename="app.log",
    filemode="w",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logging.info("Starting rematch-items.py")

PLEX_URL = os.getenv("PLEX_URL")
PLEX_TOKEN = os.getenv("PLEX_TOKEN")
LIBRARY_NAME = os.getenv("LIBRARY_NAME")
LIBRARY_NAMES = os.getenv("LIBRARY_NAMES")

if LIBRARY_NAMES:
    lib_array = LIBRARY_NAMES.split(",")
else:
    lib_array = [LIBRARY_NAME]

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


print(f"connecting to {PLEX_URL}...")
logging.info(f"connecting to {PLEX_URL}...")
plex = PlexServer(PLEX_URL, PLEX_TOKEN)
for lib in lib_array:
    print(f"getting items from [{lib}]...")
    logging.info(f"getting items from [{lib}]...")
    items = plex.library.section(lib).all()
    item_total = len(items)
    print(f"looping over {item_total} items...")
    logging.info(f"looping over {item_total} items...")
    item_count = 1

    plex_links = []
    external_links = []

    for item in items:
        tmpDict = {}
        item_count = item_count + 1
        attempts = 0

        progress_str = f"{item.title}"

        progress(item_count, item_total, progress_str)

        while attempts < 5:
            try:

                progress_str = f"{item.title} - attempt {attempts + 1}"
                logging.info(progress_str)

                progress(item_count, item_total, progress_str)

                item.fixMatch(auto=True)

                progress_str = f"{item.title} - DONE"
                progress(item_count, item_total, progress_str)

                attempts = 6
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

            attempts += 1

    print(os.linesep)
