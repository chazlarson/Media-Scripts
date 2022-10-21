# Media-Scripts

Misc scripts and tools. Undocumented scripts probably do what I need them to but aren't finished yet.

## Requirements

1. A system that can run Python 3.7
1. Python 3.7 installed on that system

One of the requirements of this script is alive-progress 2.4.1, which requires python 3.7.

## Setup

1. clone repo
1. Install requirements with `pip install -r requirements.txt` [I'd suggest doing this in a virtual environment]
1. cd to desired directory
1. Copy `.env.example` to `.env`
1. Edit .env to suit

All these scripts use the same `.env` and requirements.

TODO: move `.env` file to top level and use it from there.

.env contents
```
TMDB_KEY=TMDB_API_KEY                        # https://developers.themoviedb.org/3/getting-started/introduction
TVDB_KEY=TVDB_V4_API_KEY                     # currently not used; https://thetvdb.com/api-information
PLEX_URL=https://plex.domain.tld             # URL for Plex; can be a domain or IP:PORT
PLEX_TOKEN=PLEX-TOKEN
PLEX_OWNER=yournamehere                      # account name of the server owner
TARGET_PLEX_URL=https://plex.domain2.tld     # As above, the target of apply_all_status
TARGET_PLEX_TOKEN=PLEX-TOKEN-TWO             # As above, the target of apply_all_status
TARGET_PLEX_OWNER=yournamehere               # As above, the target of apply_all_status
LIBRARY_MAP={"LIBRARY_ON_PLEX":"LIBRARY_ON_TARGET_PLEX", ...}
                                             # In apply_all_status, map libraries according to this JSON.
LIBRARY_NAMES=Movies,TV Shows,Movies 4K      # comma-separated list of libraries to act on
CAST_DEPTH=20                                # how deep to go into the cast for actor collections
TOP_COUNT=10                                 # how many actors to export
TARGET_LABELS=this label, that label         # comma-separated list of labels to remove posters from
REMOVE_LABELS=True                           # attempt to remove the TARGET_LABELs from items after resetting the poster
DELAY=1                                      # optional delay between items
CURRENT_POSTER_DIR=current_posters           # put downloaded current posters and artwork here
POSTER_DIR=extracted_posters                 # put downloaded posters here
POSTER_DEPTH=20                              # grab this many posters [0 grabs all]
POSTER_DOWNLOAD=False                        # generate a script rather than downloading
POSTER_CONSOLIDATE=True                      # posters are separated into folders by library
TRACK_RESET_STATUS=True                      # reset-posters-* keeps track of status and picks up where it left off
ARTWORK=True                                 # current background is downloaded with current poster
PLEX_PATHS=False
NAME_IN_TITLE=True
POSTER_NAME=poster
BACKGROUND_NAME=background
RESET_SEASONS=True                           # reset-posters-plex resets season artwork as well in TV libraries
RESET_EPISODES=True                          # reset-posters-plex resets episode artwork as well in TV libraries [requires RESET_SEASONS=True]
KEEP_COLLECTIONS=bing,bang                   # List of collections to keep
INCLUDE_COLLECTION_ARTWORK=1                 # should get-all-posters retrieve collection posters?
ONLY_COLLECTION_ARTWORK=0                    # should get-all-posters retrieve ONLY collection posters?
LOCAL_RESET_ARCHIVE=1                        # should reset-posters-tmdb keep a local archive of posters?
```

## Plex scripts:

 1. user-emails.py - extract user emails from your shares
 2. reset-posters-tmdb.py - reset all artwork in a library to TMDB default
 3. reset-posters-plex.py - reset all artwork in a library to Plex default
 4. grab-current-posters.py - Grab currently-set posters and optionally background artwork
 5. grab-all-posters.py - grab some or all of the artwork for a library from plex
 6. grab-all-status.py - grab watch status for all users all libraries from plex
 7. apply-all-status.py - apply watch status for all users all libraries to plex from the file emitted by the previous script
 8. show-all-playlists.py - Show contents of all user playlists
 9. delete-collections.py - delete most or all collections from one or more libraries
10. refresh-metadata.py - Refresh metadata individually on items in a library

See the [Plex Scripts README](Plex/README.md) for details.

## Plex-Meta Manager scripts

1. extract_collections.py - extract collections from a library
2. pmm_trakt_auth.py - generate trakt auth block for PMM config.yml
3. pmm_mal_auth.py - generate mal auth block for PMM config.yml

See the [Plex-Meta-Manager Scripts README](Plex-Meta-Manager/README.md) for details.

# TMDB scripts

1. tmdb-people.py - retrieve TMDB images for a list of people

See the [TMDB Scripts README](TMDB/README.md) for details.

# Other script repos of interest

1. [bullmoose](https://github.com/bullmoose20/Plex-Stuff)
2. [Casvt](https://github.com/Casvt/Plex-scripts)
