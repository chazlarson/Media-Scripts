from plexapi.server import PlexServer
from plexapi.exceptions import Unauthorized
import os
from dotenv import load_dotenv
from helpers import get_plex

if os.path.exists(".env"):
    load_dotenv()
else:
    print(f"No environment [.env] file.  Exiting.")
    exit()

PLEX_URL = os.getenv("PLEX_URL")
PLEX_TOKEN = os.getenv("PLEX_TOKEN")
PLEX_OWNER = os.getenv("PLEX_OWNER")

print(f"connecting to {PLEX_URL}...")
plex = get_plex(PLEX_URL, PLEX_TOKEN)

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
        user_plex = get_plex(PLEX_URL, user_acct.get_token(PMI))

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
    except Exception as ex:
        handle_this_silently = "please"
