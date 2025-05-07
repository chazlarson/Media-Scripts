#!/usr/bin/env python
from logs import setup_logger, plogger

from helpers import get_all_from_library, get_plex, load_and_upgrade_env
from pathlib import Path
import random

from datetime import datetime

# current dateTime
now = datetime.now()

# convert to string
RUNTIME_STR = now.strftime("%Y-%m-%d %H:%M:%S")

SCRIPT_NAME = Path(__file__).stem

VERSION = "0.0.1"

env_file_path = Path(".env")

ACTIVITY_LOG = f"{SCRIPT_NAME}.log"
setup_logger("activity_log", ACTIVITY_LOG)

plogger(f"Starting {SCRIPT_NAME} {VERSION} at {RUNTIME_STR}", "info", "a")

if load_and_upgrade_env(env_file_path) < 0:
    exit()

plex = get_plex()
plogger("connection success", "info", "a")
plogger(f"Plex version {plex.version}", "info", "a")

new_rating = round(random.random() * 10, 1)

the_lib = plex.library.section("Test-Movies")
the_type = the_lib.type

print(f"getting first item from the {the_type} library [{the_lib.title}]...")
items = get_all_from_library(the_lib, the_type)

item = items[1][0]

item_title = item.title
print(f"Working with: {item_title}")
print(f"Random rating: {new_rating}")

audience_rating = item.audienceRating
critic_rating = item.rating
user_rating = item.userRating

print(f"current audience rating on: {item_title}: {audience_rating}")
print(f"current critic rating on: {item_title}: {critic_rating}")
print(f"current user rating on: {item_title}: {user_rating}")

print(f"setting audience rating on: {item_title} to {new_rating}")
item.editField("audienceRating", new_rating)

print(f"setting critic rating on: {item_title} to {new_rating}")
item.editField("rating", new_rating)

print(f"setting user rating on: {item_title} to {new_rating}")
item.editUserRating(new_rating, locked=False)

print(f"reloading: {item_title}")
item.reload()

print(f"retrieving ratings for: {item_title}")
user_rating = item.userRating
audience_rating = item.audienceRating
critic_rating = item.rating

print(f"current audience rating on: {item_title}: {audience_rating}")
print(f"current critic rating on: {item_title}: {critic_rating}")
print(f"current user rating on: {item_title}: {user_rating}")
