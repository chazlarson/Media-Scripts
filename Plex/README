# Plex scripts

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
LIBRARY_NAMES=Movies,TV Shows,Movies 4K      # comma-separated list of libraries to act on
CAST_DEPTH=20                                # how deep to go into the cast for actor collections
TOP_COUNT=10                                 # how many actors to export
```

## Scripts:
1. [user-emails.py](#user-emailspy) - extract user emails from your shares

## user-emails.py

You want a list of the eamil addresses for all the people you share with.

Here is a quick and dirty [emphasis on "quick" and "dirty"] way to do that.

### Usage
1. setup as above
2. Run with `python user-emails.py`

The script will loop through all the shared users on your acount and spit out username and email address.

```shell
connecting...
getting users...
looping over 26 users...
binguser - bing@gmail.com
mrbang - bang@gmail.com
boingster - boing@gmail.com
...
```

