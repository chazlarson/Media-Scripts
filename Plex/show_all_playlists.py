""" Show all playlists for all users in Plex """
#!/usr/bin/env python
from pathlib import Path
from datetime import datetime
import os
import sys
import logging
from helpers import get_plex, load_and_upgrade_env

# current dateTime
now = datetime.now()

# convert to string
RUNTIME_STR = now.strftime("%Y-%m-%d %H:%M:%S")

SCRIPT_NAME = Path(__file__).stem

VERSION = "0.1.0"


env_file_path = Path(".env")

logging.basicConfig(
    filename=f"{SCRIPT_NAME}.log",
    filemode="w",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

LOG_STR = f"Starting {SCRIPT_NAME} {VERSION} at {RUNTIME_STR}"
logging.info(LOG_STR)
print(LOG_STR)

if load_and_upgrade_env(env_file_path) < 0:
    sys.exit()

PLEX_OWNER = os.getenv("PLEX_OWNER")

plex = get_plex()

PMI = plex.machineIdentifier

account = plex.myPlexAccount()
all_users = account.users()
ITEM = None

user_ct = len(all_users)
USER_IDX = 0
for plex_user in all_users:
    user_acct = account.user(plex_user.title)
    USER_IDX += 1
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
                for ITEM in items:
                    TYPESTR = f"{ITEM.type}".ljust(7)
                    OUTPUT = ITEM.title
                    if ITEM.type == "episode":
                        OUTPUT = (
                            f"{ITEM.grandparentTitle} {ITEM.seasonEpisode} {ITEM.title}"
                        )
                    print(f"{TYPESTR} - {OUTPUT}")
    except Exception as ex: # pylint: disable=broad-exception-caught
        print(f"ERROR on {plex_user.title}: {ex}")
