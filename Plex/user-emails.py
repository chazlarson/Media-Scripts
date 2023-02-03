from plexapi.server import PlexServer
from dotenv import load_dotenv
import os
from helpers import get_plex

import logging
from pathlib import Path
SCRIPT_NAME = Path(__file__).stem

logging.basicConfig(
    filename=f"{SCRIPT_NAME}.log",
    filemode="w",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logging.info(f"Starting {SCRIPT_NAME}")
print(f"Starting {SCRIPT_NAME}")

if os.path.exists(".env"):
    load_dotenv()
else:
    print(f"No environment [.env] file.  Exiting.")
    exit()

PLEX_URL = os.getenv("PLEX_URL")
PLEX_TOKEN = os.getenv("PLEX_TOKEN")

print("connecting...")
plex = get_plex(PLEX_URL, PLEX_TOKEN)
plexacc = plex.myPlexAccount()
print("getting users...")
users = plexacc.users()
user_total = len(users)
print(f"looping over {user_total} users...")
for u in users:
    print(f"{u.username} - {u.email}")
