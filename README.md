# Media-Scripts

Misc scripts and tools. Undocumented scripts probably do what I need them to but aren't finished yet.

## Requirements

1. A system that can run Python 3.7 [or newer]
1. Python 3.7 [or newer] installed on that system

One of the requirements of these scripts is alive-progress 2.4.1, which requires Python 3.7.

## Setup

1. clone repo
1. Install requirements with `pip install -r requirements.txt` [I'd suggest doing this in a virtual environment]
1. cd to desired directory
1. Copy `.env.example` to `.env`
1. Edit .env to suit

All these scripts use the same `.env` and requirements.

## Plex scripts:

1. adjust-added-dates.py - fix broken added and perhaps originally available dates in your library
1. user-emails.py - extract user emails from your shares
1. reset-posters-tmdb.py - reset all artwork in a library to TMDB default
1. reset-posters-plex.py - reset all artwork in a library to Plex default
1. grab-all-IDs.py - grab [into a sqlite DB] ratingKey, IMDB ID, TMDB ID, TVDB ID for everything in a library from plex
1. grab-all-posters.py - grab some or all of the artwork for a library from plex
1. grab-all-status.py - grab watch status for all users all libraries from plex
1. apply-all-status.py - apply watch status for all users all libraries to plex from the file emitted by the previous script
1. show-all-playlists.py - Show contents of all user playlists
1. delete-collections.py - delete most or all collections from one or more libraries
1. refresh-metadata.py - Refresh metadata individually on items in a library
1. list-item-ids.py - Generate a list of IDs in libraries and/or collections
1. actor-count.py - Generate a list of actor credit counts
1. list_low_poster_counts.py - Generate a list of items that have fewer than some number of posters in Plex
1. image_picker.py - Flask app to make choosing asset are simpler

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
3. [maximuskowalski](https://github.com/maximuskowalski/maxmisc)
