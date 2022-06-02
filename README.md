# Media-Scripts

Misc scripts and tools. Undocumented scripts probably do what I need them to but aren't finished yet.

## Setup

1. clone repo
1. Install requirements with `pip install -r requirements.txt` [I'd suggest doing this in a virtual environment]
1. Copy `.env.example` to `.env`
1. Edit .env to suit

All these scripts use the same `.env` and requirements.

### `.env` contents

```
TMDB_KEY=TMDB_API_KEY                        # https://developers.themoviedb.org/3/getting-started/introduction
TVDB_KEY=TVDB_V4_API_KEY                     # currently not used; https://thetvdb.com/api-information
PLEX_URL=https://plex.domain.tld             # URL for Plex; can be a domain or IP:PORT
PLEX_TOKEN=PLEX-TOKEN
PLEX_OWNER=yournamehere                      # account name of the server owner
LIBRARY_NAMES=Movies,TV Shows,Movies 4K      # comma-separated list of libraries to act on
CAST_DEPTH=20                                # how deep to go into the cast for actor collections
TOP_COUNT=10                                 # how many actors to export
TARGET_LABELS=this label, that label         # comma-separated list of labels to remove posters from
REMOVE_LABELS=True                           # attempt to remove the TARGET_LABELs from items after resetting the poster
DELAY=1                                      # optional delay between items
CURRENT_POSTER_DIR=current_posters           # put downloaded current posters and artwork here
POSTER_DIR=extracted_posters                 # put downloaded posters here
POSTER_DEPTH=20                              # grab this many posters [0 grabs all]
POSTER_DOWNLOAD=0                            # if set to 0, generate a script rather than downloading
POSTER_CONSOLIDATE=1                         # if set to 0, posters are separated into folders by library
TRACK_RESET_STATUS=1                         # if set to 1, reset_posters keeps track of status and picks up where it left off
ARTWORK_AND_POSTER=1                         # if set to 1, current background is downloaded with current poster
```

## Plex scripts:

1. user-emails.py - extract user emails from your shares
2. reset-posters.py - reset all artwork in a library
3. grab-current-posters.py - Grab currently-set posters and optionally background artwork
4. grab-all-posters.py - grab some or all of the artwork for a library from plex
5. grab-all-status.py - grab watch status for all users all libraries from plex
6. apply-all-status.py - apply watch status for all users all libraries to plex from the file emitted by the previous script

See the [Plex Scripts README](Plex/README.md) for details.

## Plex-Meta Manager scripts

1. extract_collections.py - extract collections from a library
2. pmm_trakt_auth.py - generate trakt auth block for PMM config.yml
3. pmm_mal_auth.py - generate mal auth block for PMM config.yml

See the [Plex-Meta-Manager Scripts README](Plex-Meta-Manager/README.md) for details.

