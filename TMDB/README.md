# TMDB scripts

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
DELAY=1                                      # optional delay between items
POSTER_DIR=people_posters                    # put downloaded posters here
PERSON_DEPTH=10                              # how deep to go into the search results for people
```

## Scripts:
1. [tmdb-people.py](#tmdb-peoplepy) - retrieve TMDB images for a list of people

## tmdb-people.py.py

You want a bunch of person images from TMDB.

### Usage
1. setup as above
2. enter names or TMDB IDs into people_list.txt
3. Run with `python tmdb-people.py`

The script will loop through all the names in the list and download their profile images from TMDB.

```shell
 $ python tmdb-people.py
526 item(s) retrieved...
on 33: ->  exception: Archie Bunker - No Results Found
on 48: ->  exception: Benson & Moorhead - No Results Found
TMDB people |████████▌                               | █▆▄ 111/526 [21%] in 33s (3.4/s, eta: 2:03)
->   starting: Chuck Russell
```

If the name search returns more than one result, the script will attempt to download images for the first `PERSON_DEPTH` results.
