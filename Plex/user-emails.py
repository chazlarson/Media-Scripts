#!/usr/bin/env python
import logging
from datetime import datetime
from pathlib import Path

from config import Config
from helpers import get_plex

# current dateTime
now = datetime.now()

# convert to string
RUNTIME_STR = now.strftime("%Y-%m-%d %H:%M:%S")

SCRIPT_NAME = Path(__file__).stem

VERSION = "0.1.0"

logging.basicConfig(
    filename=f"{SCRIPT_NAME}.log",
    filemode="w",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logging.info(f"Starting {SCRIPT_NAME} {VERSION} at {RUNTIME_STR}")
print(f"Starting {SCRIPT_NAME} {VERSION} at {RUNTIME_STR}")

config = Config('../config.yaml')

print("connecting...")
plex = get_plex()
plexacc = plex.myPlexAccount()
print("getting users...")
users = plexacc.users()
user_total = len(users)
print(f"looping over {user_total} users...")
for u in users:
    print(f"{u.username} - {u.email}")
