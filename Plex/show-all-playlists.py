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

PLEX_OWNER = config.get("target.plex_owner")

plex = get_plex()

PMI = plex.machineIdentifier

account = plex.myPlexAccount()
all_users = account.users()
item = None

user_ct = len(all_users)
user_idx = 0
for plex_user in all_users:
    user_acct = account.user(plex_user.title)
    user_idx += 1
    try:
        user_plex = get_plex(user_acct.get_token(PMI))

        playlists = user_plex.playlists()
        if len(playlists) > 0:
            print(f"\n------------ {plex_user.title} ------------")

            for pl in playlists:
                print(
                    f"------------ {plex_user.title} playlist: {pl.title} ------------"
                )
                items = pl.items()
                for item in items:
                    typestr = f"{item.type}".ljust(7)
                    output = item.title
                    if item.type == "episode":
                        output = (
                            f"{item.grandparentTitle} {item.seasonEpisode} {item.title}"
                        )
                    print(f"{typestr} - {output}")
    except:
        handle_this_silently = "please"
