from collections import Counter
from datetime import datetime
from pathlib import Path
import platform
import time
from timeit import default_timer as timer
from alive_progress import alive_bar
from plexapi.server import PlexServer
import os
from dotenv import load_dotenv
import sys
import textwrap
from tmdbapis import TMDbAPIs

from helpers import booler, get_size, get_all_from_library, get_ids, get_letter_dir, get_plex, redact, validate_filename, load_and_upgrade_env
from logs import setup_logger, plogger, blogger, logger

TMDB_GENDER_NOT_SET = 0
TMDB_GENDER_FEMALE = 1
TMDB_GENDER_MALE = 2
TMDB_GENDER_NONBINARY = 3

# DONE 0.1.0: refactoring, added version

start = timer()

SCRIPT_NAME = Path(__file__).stem

VERSION = "0.1.0"

ACTIVITY_LOG = f"{SCRIPT_NAME}.log"

setup_logger('activity_log', ACTIVITY_LOG)

env_file_path = Path(".env")

# current dateTime
now = datetime.now()

IS_WINDOWS = platform.system() == "Windows"

# convert to string
RUNTIME_STR = now.strftime("%Y-%m-%d %H:%M:%S")

plogger(f"Starting {SCRIPT_NAME} {VERSION} at {RUNTIME_STR}", 'info', 'a')

if load_and_upgrade_env(env_file_path) < 0:
    exit()

LIBRARY_NAME = os.getenv("LIBRARY_NAME")
LIBRARY_NAMES = os.getenv("LIBRARY_NAMES")

if LIBRARY_NAMES:
    LIB_ARRAY = [s.strip() for s in LIBRARY_NAMES.split(",")]
else:
    LIB_ARRAY = [LIBRARY_NAME]

TMDB_KEY = os.getenv("TMDB_KEY")
TVDB_KEY = os.getenv("TVDB_KEY")
CAST_DEPTH = int(os.getenv("CAST_DEPTH"))
TOP_COUNT = int(os.getenv("TOP_COUNT"))
ACTORS_ONLY = booler(os.getenv("ACTORS_ONLY"))
TRACK_GENDER = booler(os.getenv("TRACK_GENDER"))

GENERATE_PMM_YAML = booler(os.getenv("GENERATE_PMM_YAML"))
NUM_COLLECTIONS = int(os.getenv("NUM_COLLECTIONS"))
MIN_GENDER_NONE = int(os.getenv("MIN_GENDER_NONE"))
MIN_GENDER_FEMALE = int(os.getenv("MIN_GENDER_FEMALE"))
MIN_GENDER_MALE = int(os.getenv("MIN_GENDER_MALE"))
MIN_GENDER_NB = int(os.getenv("MIN_GENDER_NB"))

if (MIN_GENDER_NONE + MIN_GENDER_FEMALE + MIN_GENDER_MALE + MIN_GENDER_NB) > NUM_COLLECTIONS:
    print("minimum geneder req uirements exceed number of collections")
    exit(1)

DELAY = int(os.getenv("DELAY"))

if not DELAY:
    DELAY = 0

tmdb = TMDbAPIs(TMDB_KEY, language="en")

tmdb_str = "tmdb://"
tvdb_str = "tvdb://"

actors = Counter()
casts = Counter()
gender_none = Counter()
gender_female = Counter()
gender_male = Counter()
gender_nonbinary = Counter()

def track_gender(the_key, gender):
    if gender == TMDB_GENDER_NOT_SET:
        gender_none[the_key] += 1
        
    if gender == TMDB_GENDER_FEMALE:
        gender_female[the_key] += 1
        
    if gender == TMDB_GENDER_MALE:
        gender_male[the_key] += 1
        
    if gender == TMDB_GENDER_NONBINARY:
        gender_nonbinary[the_key] += 1

def translate_gender(gender):
    if gender == TMDB_GENDER_NOT_SET:
        return 'Unknown/Not set'
        
    if gender == TMDB_GENDER_FEMALE:
        return 'Female'
        
    if gender == TMDB_GENDER_MALE:
        return 'Male'
        
    if gender == TMDB_GENDER_NONBINARY:
        return 'Non-binary'

def reverse_gender(gender_str):
    if gender_str == 'Unknown/Not set':
        return TMDB_GENDER_NOT_SET
        
    if gender_str == 'Female':
        return TMDB_GENDER_FEMALE
        
    if gender_str == 'Male':
        return TMDB_GENDER_MALE
        
    if gender_str == 'Non-binary':
        return TMDB_GENDER_NONBINARY

def getTID(theList):
    tmid = None
    tvid = None
    for guid in theList:
        if tmdb_str in guid.id:
            tmid = guid.id.replace(tmdb_str, "")
        if tvdb_str in guid.id:
            tvid = guid.id.replace(tvdb_str, "")
    return tmid, tvid

plex = get_plex()

ALL_LIBS = plex.library.sections()
ALL_LIB_NAMES = []

plogger(f"{len(ALL_LIBS)} libraries found:", 'info', 'a')
for lib in ALL_LIBS:
    ALL_LIB_NAMES.append(f"{lib.title.strip()}")

if LIBRARY_NAMES == 'ALL_LIBRARIES':
    LIB_ARRAY = []
    for lib in ALL_LIBS:
        LIB_ARRAY.append(lib.title.strip())

def ascii_histogram(data) -> None:
    """A horizontal frequency-table/histogram plot."""
    for k in sorted(data):
        print('{0} {1}'.format(k, '+' * data[k]))


for lib in LIB_ARRAY:
    print(f"getting items from [{lib}]...")
    the_lib = plex.library.section(lib)
    items = get_all_from_library(plex, the_lib)

    item_total = len(items)
    print(f"looping over {item_total} items...")
    print(f"tracking gender: {TRACK_GENDER}")
    item_count = 1
    cast_count = 0
    credit_count = 0
    skip_count = 0
    highwater_cast = 0
    total_cast = 0
    average_cast = 0
    with alive_bar(item_total, dual_line=True, title=f"Actor Count: {lib}") as bar:
        for item in items:
            tmpDict = {}
            tmdb_id, tvdb_id = getTID(item.guids)
            item_count = item_count + 1
            try:
                cast = ""
                if item.TYPE == "show":
                    cast = tmdb.tv_show(tmdb_id).cast
                else:
                    cast = tmdb.movie(tmdb_id).cast
                count = 0
                cast_size = len(cast)

                if cast_size < 2:
                    print(f"small cast - {item.title}: {cast_size}")
                casts[f"{cast_size:5d}"] += 1
                total_cast += cast_size
                average_cast = round(total_cast / item_count)
                if cast_size > highwater_cast:
                    highwater_cast = cast_size
                    print(f"New cast size high water mark - {item.title}: {highwater_cast}")

                bar.text(f"Processing {CAST_DEPTH if CAST_DEPTH < cast_size else cast_size} of {cast_size} from {item.title} - average cast {average_cast} counts: {len(actors)} - N{len(gender_none)} - F{len(gender_female)} - M{len(gender_male)} - NB{len(gender_nonbinary)}")
                for actor in cast:
                    # actor points to person

                    if count < CAST_DEPTH:
                        count = count + 1
                        cast_count += 1
                        the_key = f"{actor.name} - {actor.person_id} - {translate_gender(gender)}"
                        count_them = False
                        if ACTORS_ONLY:
                            if actor.known_for_department == "Acting":
                                count_them = True
                            else:
                                skip_count += 1
                                print(f"Skipping {actor.name}: {actor.known_for_department}")
                        else:
                            count_them = True

                        if count_them:
                            actors[the_key] += 1
                            if TRACK_GENDER:
                                track_gender(the_key, actor.gender)
                            credit_count += 1
                            bar.text(f"Processing {CAST_DEPTH if CAST_DEPTH < cast_size else cast_size} of {cast_size} from {item.title} - average cast {average_cast} counts: {len(actors)} - N{len(gender_none)} - F{len(gender_female)} - M{len(gender_male)} - NB{len(gender_nonbinary)}")
            except Exception as ex:
                print(f"{item_count}, {item_total}, EX: {item.title}")

            bar()

            # Wait between items in case hammering the Plex server turns out badly.
            time.sleep(DELAY)

    print("\r\r")

    end = timer()
    elapsed = end - start
    print(f"Looked at {cast_count} credits from the top {CAST_DEPTH} from each {the_lib.TYPE} in {elapsed} seconds.")
    print(f"Unique people: {len(actors)}")
    print(f"'None' gender': {len(gender_none)}")
    print(f"'Female' gender': {len(gender_female)}")
    print(f"'Male' gender': {len(gender_male)}")
    print(f"'Nonbinary' gender': {len(gender_nonbinary)}")
    print(f"Unique cast counts: {len(casts)}")
    print(f"Longest cast list: {highwater_cast}")
    print(f"Average cast list: {average_cast}")
    print(f"Skipped {skip_count} non-actors")
    print(f"Total {credit_count} credits recorded")
    print(f"Top {TOP_COUNT} listed below")


    count = 0
    for actor in sorted(actors.items(), key=lambda x: x[1], reverse=True):
        if count < TOP_COUNT:
            print("{}\t{}".format(actor[1], actor[0]))
            count = count + 1

    print("--------------------------------\ncast sizes with relative frequency\n--------------------------------")
    ascii_histogram(casts)
    print("--------------------------------\n")
    
    if GENERATE_PMM_YAML:
        top_actors = Counter()

        count = 0
        if MIN_GENDER_NONE > 0:
            for actor in sorted(gender_none.items(), key=lambda x: x[1], reverse=True):
                if count < MIN_GENDER_NONE:
                    top_actors[actor[0]] = actor[1]
                    count = count + 1

        count = 0
        if MIN_GENDER_FEMALE > 0:
            for actor in sorted(gender_female.items(), key=lambda x: x[1], reverse=True):
                if count < MIN_GENDER_FEMALE:
                    top_actors[actor[0]] = actor[1]
                    count = count + 1

        count = 0
        if MIN_GENDER_MALE > 0:
            for actor in sorted(gender_male.items(), key=lambda x: x[1], reverse=True):
                if count < MIN_GENDER_MALE:
                    top_actors[actor[0]] = actor[1]
                    count = count + 1

        count = 0
        if MIN_GENDER_NB > 0:
            for actor in sorted(gender_nonbinary.items(), key=lambda x: x[1], reverse=True):
                if count < MIN_GENDER_NB:
                    top_actors[actor[0]] = actor[1]
                    count = count + 1

        if len(top_actors) < NUM_COLLECTIONS:
            for actor in sorted(actors.items(), key=lambda x: x[1], reverse=True):
                if len(top_actors) == NUM_COLLECTIONS:
                    break
                if actor[0] not in top_actors.keys():
                    top_actors[actor[0]] = actor[1]

        print(f"--------------------------------")
        collection_string = "- pmm: actor\n  template_variables:\n    include:\n"
        print(f"Top {NUM_COLLECTIONS} actors with genders accounted for")
        for actor in sorted(top_actors.items(), key=lambda x: x[1], reverse=True):
            if count < TOP_COUNT:
                print("{}\t{}".format(actor[1], actor[0]))
                bits = actor[0].split(' - ')
                collection_string = f"{collection_string}        - {bits[0]}\n"
                count = count + 1

        print(f"--------------------------------")
        
        print(f"Creating {NUM_COLLECTIONS} with:")
        print(f"Minimum {MIN_GENDER_FEMALE} female actors if possible")
        print(f"Minimum {MIN_GENDER_MALE} male actors if possible")
        print(f"Minimum {MIN_GENDER_NB} non-binary actors if possible")
        print(f"Minimum {MIN_GENDER_NONE} no-gender-available actors if possible")
        
        print(f"--- YAML FOR PMM config.yml ----")
        
        print(collection_string)

        print(f"--- END YAML -------------------")
