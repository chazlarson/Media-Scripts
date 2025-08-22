#!/usr/bin/env python
# -*- coding: utf-8 -*-

import platform
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from timeit import default_timer as timer

from alive_progress import alive_bar
from config import Config
from helpers import (get_all_from_library, get_ids, get_plex,
                     get_target_libraries)
from logs import plogger, setup_logger
from tmdbapis import TMDbAPIs

TMDB_GENDER_NOT_SET = 0
TMDB_GENDER_FEMALE = 1
TMDB_GENDER_MALE = 2
TMDB_GENDER_NONBINARY = 3

JOB_ACTOR = "Actor"
JOB_DIRECTOR = "Director"

# DONE 0.1.0: refactoring, added version
# DONE 0.2.0: config class

start = timer()

SCRIPT_NAME = Path(__file__).stem

VERSION = "0.1.0"

ACTIVITY_LOG = f"{SCRIPT_NAME}.log"

setup_logger("activity_log", ACTIVITY_LOG)

# current dateTime
now = datetime.now()

# convert to string
RUNTIME_STR = now.strftime("%Y-%m-%d %H:%M:%S")

IS_WINDOWS = platform.system() == "Windows"

plogger(f"Starting {SCRIPT_NAME} {VERSION} at {RUNTIME_STR}", "info", "a")

config = Config('../config.yaml')

CAST_DEPTH = config.get_int("actor.cast_depth")
TOP_COUNT = config.get_int("actor.top_count")
TRACK_GENDER = config.get_bool("actor.track_gender")

NUM_COLLECTIONS = config.get_int("general.num_collections")
MIN_GENDER_NO_GENDER = config.get_int("general.min_gender_no_gender", 0)
MIN_GENDER_FEMALE = config.get_int("general.min_gender_female", 0)
MIN_GENDER_MALE = config.get_int("general.min_gender_male", 0)
MIN_GENDER_NB = config.get_int("general.min_gender_nb", 0)

if (
    MIN_GENDER_NO_GENDER + MIN_GENDER_FEMALE + MIN_GENDER_MALE + MIN_GENDER_NB
) > NUM_COLLECTIONS:
    print("minimum gender requirements exceed number of collections")
    exit(1)

DELAY = config.get_int("general.delay", 0)

tmdb = TMDbAPIs(str(config.get("general.tmdb_key", "NO_KEY_SPECIFIED")), language="en")

people = Counter()
lists = Counter()
gender_no_gender = Counter()
gender_female = Counter()
gender_male = Counter()
gender_nonbinary = Counter()


def track_gender(the_key, gender):
    if gender == TMDB_GENDER_NOT_SET:
        gender_no_gender[the_key] += 1

    if gender == TMDB_GENDER_FEMALE:
        gender_female[the_key] += 1

    if gender == TMDB_GENDER_MALE:
        gender_male[the_key] += 1

    if gender == TMDB_GENDER_NONBINARY:
        gender_nonbinary[the_key] += 1


def translate_gender(gender):
    if gender == TMDB_GENDER_NOT_SET:
        return "Unknown/Not set"

    if gender == TMDB_GENDER_FEMALE:
        return "Female"

    if gender == TMDB_GENDER_MALE:
        return "Male"

    if gender == TMDB_GENDER_NONBINARY:
        return "Non-binary"


def reverse_gender(gender_str):
    if gender_str == "Unknown/Not set":
        return TMDB_GENDER_NOT_SET

    if gender_str == "Female":
        return TMDB_GENDER_FEMALE

    if gender_str == "Male":
        return TMDB_GENDER_MALE

    if gender_str == "Non-binary":
        return TMDB_GENDER_NONBINARY


plex = get_plex()


LIB_ARRAY = get_target_libraries(plex)


def ascii_histogram(data) -> None:
    """A horizontal frequency-table/histogram plot."""
    for k in sorted(data):
        print("{0} {1}".format(k, "+" * data[k]))


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
            imdbid, tmid, tvid = get_ids(item.guids)
            item_count = item_count + 1
            try:
                list = ""
                if item.TYPE == "show":
                    media_item = tmdb.tv_show(tmid) if tmid else None
                else:
                    media_item = tmdb.movie(tmid) if tmid else None
                if config.get("actor.job_type") == JOB_DIRECTOR:
                    person_data = media_item.crew if media_item else []
                else:
                    person_data = media_item.cast if media_item else []
                if person_data is None:
                    person_list = []
                else:
                    person_list = person_data if person_data else []

                count = 0
                list_size = len(person_list) if person_list else 0

                if list_size < 2:
                    print(f"small list - {item.title}: {list_size}")
                lists[f"{list_size:5d}"] += 1
                total_list += list_size
                average_list = round(total_list / item_count)
                if list_size > highwater_list:
                    highwater_list = list_size
                    print(
                        f"New list size high water mark - {item.title}: {highwater_list}"
                    )

                bar.text(
                    f"Processing {CAST_DEPTH if CAST_DEPTH < list_size else list_size} of {list_size} from {item.title} - average list {average_list} counts: {len(people)} - N{len(gender_no_gender)} - F{len(gender_female)} - M{len(gender_male)} - NB{len(gender_nonbinary)}"
                )
                person_list = person_list[:CAST_DEPTH] if CAST_DEPTH < list_size else person_list

                for person in person_list:
                    # person points to person

                    list_count += 1
                    the_key = f"{person.name} - {person.person_id} - {translate_gender(person.gender)}"
                    count_them = False
                    if config.get_bool("actor.known_for_only"):
                        if person.known_for_department == "Acting":
                            count_them = True
                        else:
                            skip_count += 1
                            print(
                                f"Skipping {person.name}: {person.known_for_department}"
                            )
                    else:
                        count_them = True

                    if count_them:
                        people[the_key] += 1
                        if TRACK_GENDER:
                            track_gender(the_key, person.gender)
                        credit_count += 1
                        bar.text(
                            f"Processing {CAST_DEPTH if CAST_DEPTH < list_size else list_size} of {list_size} from {item.title} - average list {average_list} counts: {len(people)} - N{len(gender_no_gender)} - F{len(gender_female)} - M{len(gender_male)} - NB{len(gender_nonbinary)}"
                        )
            except Exception:
                print(f"{item_count}, {item_total}, EX: {item.title}")

            bar()

            # Wait between items in case hammering the Plex server turns out badly.
            time.sleep(DELAY)

    print("\r\r")

    end = timer()
    elapsed = end - start
    print(
        f"Looked at {list_count} credits from the top {CAST_DEPTH} from each {the_lib.TYPE} in {elapsed} seconds."
    )
    print(f"Unique people: {len(people)}")
    if TRACK_GENDER:
        print(f"'None' gender': {len(gender_no_gender)}")
        print(f"'Female' gender': {len(gender_female)}")
        print(f"'Male' gender': {len(gender_male)}")
        print(f"'Nonbinary' gender': {len(gender_nonbinary)}")
    print(f"Unique list counts: {len(lists)}")
    print(f"Longest list count: {highwater_list}")
    print(f"Average list count: {average_list}")
    print(f"Skipped {skip_count} non-primary")
    print(f"Total {credit_count} credits recorded")
    print(f"Top {TOP_COUNT} listed below")

    count = 0
    for person in sorted(people.items(), key=lambda x: x[1], reverse=True):
        if count < TOP_COUNT:
            print("{}\t{}".format(person[1], person[0]))
            count = count + 1

    print(
        "--------------------------------\nlist sizes with relative frequency\n--------------------------------"
    )
    ascii_histogram(lists)
    print("--------------------------------\n")

    if config.get_bool("general.generate_kometa_yaml"):
        top_people = Counter()

        count = 0
        if MIN_GENDER_NO_GENDER > 0:
            for person in sorted(gender_no_gender.items(), key=lambda x: x[1], reverse=True):
                if count < MIN_GENDER_NO_GENDER:
                    top_people[person[0]] = person[1]
                    count = count + 1

        count = 0
        if MIN_GENDER_FEMALE > 0:
            for person in sorted(
                gender_female.items(), key=lambda x: x[1], reverse=True
            ):
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
            for person in sorted(
                gender_nonbinary.items(), key=lambda x: x[1], reverse=True
            ):
                if count < MIN_GENDER_NB:
                    top_people[person[0]] = person[1]
                    count = count + 1

        if len(top_people) < NUM_COLLECTIONS:
            for person in sorted(people.items(), key=lambda x: x[1], reverse=True):
                if len(top_people) == NUM_COLLECTIONS:
                    break
                if person[0] not in top_people.keys():
                    top_people[person[0]] = person[1]

        print("--------------------------------")
        collection_string = "- default: actor\n  template_variables:\n    include:\n"
        print(f"Top {NUM_COLLECTIONS} people with genders accounted for")
        for person in sorted(top_people.items(), key=lambda x: x[1], reverse=True):
            if count < TOP_COUNT:
                print("{}\t{}".format(person[1], person[0]))
                bits = person[0].split(" - ")
                collection_string = f"{collection_string}        - {bits[0]}\n"
                count = count + 1

        print("--------------------------------")

        print(f"Creating {NUM_COLLECTIONS} with:")
        print(f"Minimum {MIN_GENDER_FEMALE} female people if possible")
        print(f"Minimum {MIN_GENDER_MALE} male people if possible")
        print(f"Minimum {MIN_GENDER_NB} non-binary people if possible")
        print(f"Minimum {MIN_GENDER_NO_GENDER} no-gender-available people if possible")

        print("--- YAML FOR Kometa config.yml ----")

        print(collection_string)

        print("--- END YAML -------------------")
