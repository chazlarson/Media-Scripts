#!/usr/bin/env python
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

JOB_ACTOR = "Actor"
JOB_DIRECTOR = "Director"

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

tmdb_key = os.getenv("TMDB_KEY")
TVDB_KEY = os.getenv("TVDB_KEY")
CAST_DEPTH = int(os.getenv("CAST_DEPTH"))
TOP_COUNT = int(os.getenv("TOP_COUNT"))
KNOWN_FOR_ONLY = booler(os.getenv("KNOWN_FOR_ONLY"))
TRACK_GENDER = booler(os.getenv("TRACK_GENDER"))
JOB_TYPE = os.getenv("JOB_TYPE")

GENERATE_KOMETA_YAML = booler(os.getenv("GENERATE_KOMETA_YAML"))
NUM_COLLECTIONS = int(os.getenv("NUM_COLLECTIONS"))
MIN_GENDER_NONE = int(os.getenv("MIN_GENDER_NONE"))
MIN_GENDER_FEMALE = int(os.getenv("MIN_GENDER_FEMALE"))
MIN_GENDER_MALE = int(os.getenv("MIN_GENDER_MALE"))
MIN_GENDER_NB = int(os.getenv("MIN_GENDER_NB"))

if (MIN_GENDER_NONE + MIN_GENDER_FEMALE + MIN_GENDER_MALE + MIN_GENDER_NB) > NUM_COLLECTIONS:
    print("minimum gender requirements exceed number of collections")
    exit(1)

DELAY = int(os.getenv("DELAY"))

if not DELAY:
    DELAY = 0

tmdb = TMDbAPIs(TMDB_KEY, language="en")

TMDB_STR = "tmdb://"
TVDB_STR = "tvdb://"

people = Counter()
lists = Counter()
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

def getTID(the_list):
    tmid = None
    tvid = None
    for guid in the_list:
        if TMDB_STR in guid.id:
            tmid = guid.id.replace(TMDB_STR, "")
        if TVDB_STR in guid.id:
            tvid = guid.id.replace(TVDB_STR, "")
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
    item_total, items = get_all_from_library(the_lib)

    print(f"looping over {item_total} items...")
    print(f"tracking gender: {TRACK_GENDER}")
    item_count = 1
    list_count = 0
    credit_count = 0
    skip_count = 0
    highwater_list = 0
    total_list = 0
    average_list = 0
    with alive_bar(item_total, dual_line=True, title=f"Actor Count: {lib}") as bar:
        for item in items:
            tmpDict = {}
            tmdb_id, tvdb_id = getTID(item.guids)
            item_count = item_count + 1
            try:
                list = ""
                if item.TYPE == "show":
                    media_item = tmdb.tv_show(tmdb_id)
                else:
                    media_item = tmdb.movie(tmdb_id)
                if JOB_TYPE == JOB_DIRECTOR:
                    list = media_item.crew
                else:
                    list = media_item.cast

                count = 0
                list_size = len(list)

                if list_size < 2:
                    print(f"small list - {item.title}: {list_size}")
                lists[f"{list_size:5d}"] += 1
                total_list += list_size
                average_list = round(total_list / item_count)
                if list_size > highwater_list:
                    highwater_list = list_size
                    print(f"New list size high water mark - {item.title}: {highwater_list}")

                bar.text(f"Processing {CAST_DEPTH if CAST_DEPTH < list_size else list_size} of {list_size} from {item.title} - average list {average_list} counts: {len(people)} - N{len(gender_none)} - F{len(gender_female)} - M{len(gender_male)} - NB{len(gender_nonbinary)}")
                for person in list:
                    # person points to person

                    if count < CAST_DEPTH:
                        count = count + 1
                        list_count += 1
                        the_key = f"{person.name} - {person.person_id} - {translate_gender(person.gender)}"
                        count_them = False
                        if KNOWN_FOR_ONLY:
                            if person.known_for_department == "Acting":
                                count_them = True
                            else:
                                skip_count += 1
                                print(f"Skipping {person.name}: {person.known_for_department}")
                        else:
                            count_them = True

                        if count_them:
                            people[the_key] += 1
                            if TRACK_GENDER:
                                track_gender(the_key, person.gender)
                            credit_count += 1
                            bar.text(f"Processing {CAST_DEPTH if CAST_DEPTH < list_size else list_size} of {list_size} from {item.title} - average list {average_list} counts: {len(people)} - N{len(gender_none)} - F{len(gender_female)} - M{len(gender_male)} - NB{len(gender_nonbinary)}")
            except Exception as ex:
                print(f"{item_count}, {item_total}, EX: {item.title}")

            bar() # pylint: disable=not-callable
 
            # Wait between items in case hammering the Plex server turns out badly.
            time.sleep(DELAY)

    print("\r\r")

    end = timer()
    elapsed = end - start
    print(f"Looked at {list_count} credits from the top {CAST_DEPTH} from each {the_lib.TYPE} in {elapsed} seconds.")
    print(f"Unique people: {len(people)}")
    if TRACK_GENDER:
        print(f"'None' gender': {len(gender_none)}")
        print(f"'Female' gender': {len(gender_female)}")
        print(f"'Male' gender': {len(gender_male)}")
        print(f"'Nonbinary' gender': {len(gender_nonbinary)}")
    print(f"Unique list counts: {len(lists)}")
    print(f"Longest list list: {highwater_list}")
    print(f"Average list list: {average_list}")
    print(f"Skipped {skip_count} non-primary")
    print(f"Total {credit_count} credits recorded")
    print(f"Top {TOP_COUNT} listed below")


    count = 0
    for person in sorted(people.items(), key=lambda x: x[1], reverse=True):
        if count < TOP_COUNT:
            print("{}\t{}".format(person[1], person[0]))
            count = count + 1

    print("--------------------------------\nlist sizes with relative frequency\n--------------------------------")
    ascii_histogram(lists)
    print("--------------------------------\n")

    if GENERATE_KOMETA_YAML:
        top_people = Counter()

        count = 0
        if MIN_GENDER_NONE > 0:
            for person in sorted(gender_none.items(), key=lambda x: x[1], reverse=True):
                if count < MIN_GENDER_NONE:
                    top_people[person[0]] = person[1]
                    count = count + 1

        count = 0
        if MIN_GENDER_FEMALE > 0:
            for person in sorted(gender_female.items(), key=lambda x: x[1], reverse=True):
                if count < MIN_GENDER_FEMALE:
                    top_people[person[0]] = person[1]
                    count = count + 1

        count = 0
        if MIN_GENDER_MALE > 0:
            for person in sorted(gender_male.items(), key=lambda x: x[1], reverse=True):
                if count < MIN_GENDER_MALE:
                    top_people[person[0]] = person[1]
                    count = count + 1

        count = 0
        if MIN_GENDER_NB > 0:
            for person in sorted(gender_nonbinary.items(), key=lambda x: x[1], reverse=True):
                if count < MIN_GENDER_NB:
                    top_people[person[0]] = person[1]
                    count = count + 1

        if len(top_people) < NUM_COLLECTIONS:
            for person in sorted(people.items(), key=lambda x: x[1], reverse=True):
                if len(top_people) == NUM_COLLECTIONS:
                    break
                if person[0] not in top_people.keys():
                    top_people[person[0]] = person[1]

        print(f"--------------------------------")
        collection_string = "- default: actor\n  template_variables:\n    include:\n"
        print(f"Top {NUM_COLLECTIONS} people with genders accounted for")
        for person in sorted(top_people.items(), key=lambda x: x[1], reverse=True):
            if count < TOP_COUNT:
                print("{}\t{}".format(person[1], person[0]))
                bits = person[0].split(' - ')
                collection_string = f"{collection_string}        - {bits[0]}\n"
                count = count + 1

        print(f"--------------------------------")

        print(f"Creating {NUM_COLLECTIONS} with:")
        print(f"Minimum {MIN_GENDER_FEMALE} female people if possible")
        print(f"Minimum {MIN_GENDER_MALE} male people if possible")
        print(f"Minimum {MIN_GENDER_NB} non-binary people if possible")
        print(f"Minimum {MIN_GENDER_NONE} no-gender-available people if possible")

        print(f"--- YAML FOR Kometa config.yml ----")

        print(collection_string)

        print(f"--- END YAML -------------------")
