from plexapi.server import PlexServer
from dotenv import load_dotenv
import os
from helpers import get_plex

load_dotenv()

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
