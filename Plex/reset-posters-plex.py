from plexapi.server import PlexServer
import os
from dotenv import load_dotenv
import sys
import textwrap
# from tmdbapis import TMDbAPIs
from timeit import default_timer as timer
import time

start = timer()

load_dotenv()

def boolean_string(s):
    if s not in {'False', 'True'}:
        raise ValueError('Not a valid boolean string')
    return s == 'True'

PLEX_URL = os.getenv('PLEX_URL')

if PLEX_URL is None:
    print("Your .env file is incomplete or missing: PLEX_URL is empty")
    exit()

PLEX_TOKEN = os.getenv('PLEX_TOKEN')
LIBRARY_NAME = os.getenv('LIBRARY_NAME')
LIBRARY_NAMES = os.getenv('LIBRARY_NAMES')
TARGET_LABELS = os.getenv('TARGET_LABELS')
TRACK_RESET_STATUS = os.getenv('TRACK_RESET_STATUS')
REMOVE_LABELS = boolean_string(os.getenv('REMOVE_LABELS'))
DELAY = 0
try:
    DELAY = int(os.getenv('DELAY'))
except:
    DELAY = 0

if TARGET_LABELS:
    lbl_array = TARGET_LABELS.split(",")
else:
    lbl_array = ["xy22y1973"]

if LIBRARY_NAMES:
    lib_array = LIBRARY_NAMES.split(",")
else:
    lib_array = [LIBRARY_NAME]

def progress(count, total, status=''):
    bar_len = 40
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)
    stat_str = textwrap.shorten(status, width=60)

    sys.stdout.write('[%s] %s%s ... %s\r' % (bar, percents, '%', stat_str.ljust(60)))
    sys.stdout.flush()

from pathlib import Path

print(f"connecting to {PLEX_URL}...")
plex = PlexServer(PLEX_URL, PLEX_TOKEN)
for lib in lib_array:
    id_array = []
    status_file_name = plex.library.section(lib).uuid + ".txt"
    status_file = Path(status_file_name)

    if status_file.is_file():
        with open(f"{status_file_name}") as fp:
            for line in fp:
                id_array.append(line.strip())

    print(f"{os.linesep}getting items from [{lib}]...")

    for lbl in lbl_array:
        if lbl == "xy22y1973":
            items = plex.library.section(lib).all()
            REMOVE_LABELS = False
        else:
            print(f"{os.linesep}labelled [{lbl}]...")
            items = plex.library.section(lib).search(label=lbl)
        item_total = len(items)
        print(f"looping over {item_total} items...")
        item_count = 1
        for item in items:
            item_count = item_count + 1
            if id_array.count(f"{item.ratingKey}") == 0:
                id_array.append(item.ratingKey)

                try:
                    progress(item_count, item_total, item.title)
                    pp = None
                    local_file = None

                    progress(item_count, item_total, item.title + " - getting posters")
                    posters = item.posters()
                    progress(item_count, item_total, item.title + " - setting poster")
                    item.setPoster(posters[0])

                    if REMOVE_LABELS:
                        progress(item_count, item_total, item.title + " - removing label")
                        item.removeLabel(lbl, True)

                    # write out item_array to file.
                    with open(status_file, "a") as sf:
                        sf.write(f"{item.ratingKey}{os.linesep}")

                except Exception as ex:
                    progress(item_count, item_total, "EX: " + item.title)

                # Wait between items in case hammering the Plex server turns out badly.
                time.sleep(DELAY)

    # delete the status file
    os.remove(status_file)

end = timer()
elapsed = end - start
print(f"{os.linesep}{os.linesep}processed {item_count - 1} items in {elapsed} seconds.")
