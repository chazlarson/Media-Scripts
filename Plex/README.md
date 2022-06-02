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
PLEX_OWNER=yournamehere                      # account name of the server owner
LIBRARY_NAMES=Movies,TV Shows,Movies 4K      # comma-separated list of libraries to act on
CAST_DEPTH=20                                # how deep to go into the cast for actor collections
TOP_COUNT=10                                 # how many actors to export
TARGET_LABELS=this label, that label         # comma-separated list of labels to remove posters from
REMOVE_LABELS=True                           # attempt to remove the TARGET_LABELs from items after resetting the poster
DELAY=1                                      # optional delay between items
POSTER_DIR=extracted_posters                 # put downloaded posters here
POSTER_DEPTH=20                              # grab this many posters [0 grabs all]
POSTER_DOWNLOAD=0                            # if set to 0, generate a script rather than downloading
POSTER_CONSOLIDATE=1                         # if set to 0, posters are separated into folders by library
```

## Scripts:
1. [user-emails.py](#user-emailspy) - extract user emails from your shares
1. [reset-posters.py](#reset-posterspy) - reset all artwork in a library
1. [grab-current-posters.py](#grab-current-posterspy) - Grab currently-set posters and optionally background artwork
1. [grab-all-posters.py](#grab-all-posterspy) - grab some or all of the artwork for a library from plex
2. [grab-all-status.py](#grab-all-statuspy) - grab watch status for all users all libraries from plex
3. [apply-all-status.py](#apply-all-statuspy) - apply watch status for all users all libraries to plex from the file emitted by the previous script

## user-emails.py

You want a list of email addresses for all the people you share with.

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

## reset-posters.py

Perhaps you want to reset all the posters in a library

This script will set the poster for every series or movie to the default poster from TMDB/TVDB.  It also saves that poster under `./posters/[movies|shows]/<rating_key>.ext` in case you want to use them with PMM's overlay resets.

If there is a file already located at `./posters/[movies|shows]/<rating_key>.ext`, the script will use *that image* instead of retrieving a new one, so if you replace that local one with a poster of your choice, the script will use the custom one rather than the TMDB/TVDB default.

Script-specific variables in .env:
```
TRACK_RESET_STATUS=True                         # pick up where the script left off
TARGET_LABELS = Bing, Bang, Boing               # reset artwork on items with these labels
REMOVE_LABELS=True                              # remove labels when done [NOT RECOMMENDED]
```

If you set:
```
TRACK_RESET_STATUS=True
```
The script will keep track of where it is and will pick up at that point on subsequent runs.  This is useful in the event of a lost connection to Plex.

Once it gets to the end of hte library successfully, the tracking file is deleted.

If you specify a comma-separated list of labels in the env file:
```
TARGET_LABELS = This label, That label, Another label
```
The script will reset posters only on movies with those labels assigned.

If you also set:
```
REMOVE_LABELS=True
```
The script will *attempt* to remove those labels after resetting the poster.  I say "attempt" since in testing I have experienced an odd situation where no error occurs but the label is not removed.  My test library of 230 4K-Dolby Movies contains 47 that fail in this way; every run it goes through the 47 movies "removing labels" without error yet they still have the labels on the next run.

Besides that Heisenbug, I don't recommend using this [`REMOVE_LABELS`] since the label removal takes a long time [dozens of seconds per item].  Doing this through the Plex UI is much faster.

### Usage
1. setup as above
2. Run with `python reset-posters.py`

```
tmdb config...
connecting to https://stream.BING.BANG...
getting items from [TV Shows - 4K]...
looping over 876 items...
[=---------------------------------------] 2.7% ... Age of Big Cats
```

At this time, there is no configuration aside from library name; it replaces all posters.  It does not delete any posters from Plex, just grabs a URL and uses the API to set the poster to the URL.

## grab-current-posters.py

Perhaps you want to get local copies of the currently-set posters [and maybe backgrounds] for everything in a library.

Maybe you find it easier to look through a bunch of options in CoverFlow or something.

Script-specific variables in .env:
```
CURRENT_POSTER_DIR=current_posters           # put downloaded posters here
POSTER_DOWNLOAD=0                            # if set to 0, generate a script rather than downloading
POSTER_CONSOLIDATE=1                         # if set to 0, posters are separated into folders by library
ARTWORK_AND_POSTER=1                         # if set to 1, posters and background artwork are retrieved
```

If "POSTER_DOWNLOAD" is `0`, the script will build a shell script for each library to download the images at your convenience instead of downloading them as it runs, so you can run the downloads overnight or on a different machine with ALL THE DISK SPACE or something.

If "POSTER_CONSOLIDATE" is `1`, the script will store all the images in one directory rather than separating them by library name.  The idea is that Plex shows the same set of posters for "Star Wars" whether it's in your "Movies" or "Movies - 4K" or whatever other libraries, so there's no reason to pull the same set of posters multiple times.  There is an example below.

If "ARTWORK_AND_POSTER" is `1`, the script will also grab the background artwork.

### Usage
1. setup as above
2. Run with `python grab-current-posters.py`

```
connecting to https://stream.BING.BANG...
getting items from [Movies - 4K]...
looping over 3254 items...
[----------------------------------------] 0.2% ... The 3 Worlds of Gulliver - DOWNLOADING 18974-36224-1841313-BG-Movies - 4K.png
```

he posters will be sorted by library [if enabled] with each poster getting an incremented number, like this:

The image names are: `TMDBID-TVDBID-RATINGKEY-INCREMENT.ext`

POSTER_CONSOLIDATE=1:
```
current_posters
└── all_libraries
    ├── 100402-Captain America The Winter Soldier
    │   ├── 100402-965-1456628-Movies - 4K.png
    │   └── 100402-965-1456628-BG-Movies - 4K.png
    ├── 10061-Escape from L.A
    │   ├── 10061-2520-1985150-Movies - 4K.png
    │   └── 10061-2520-1985150-BG-Movies - 4K.png
...
```

POSTER_CONSOLIDATE=0:
```
extracted_posters
├── Movies - 4K
│   └── 100402-Captain America The Winter Soldier
│       ├── 100402-965-1456628.png
│       └── 100402-965-1456628-BG.png
└── Movies - 1080p
    └── 10061-Escape from L.A
        ├── 10061-2520-1985150.png
        └── 10061-2520-1985150-BG.png
...
```
## grab-all-posters.py

Perhaps you want to get local copies of some or all the posters Plex knows about for everything in a library.

Maybe you find it easier to look through a bunch of options in CoverFlow or something.

This script will download some or all the posters for every item in a given set of libraries.  It (probably) won't download the same thing more than once, so you can cancel it and restart it if need be.  I say "probably" because the script is assuming that the list of posters retireved from Plex is always in the same order [i.e. that new posters get appended to the end of the list].  On subsequent runs, the script checks only that a file exists at, for example, `extracted_posters/Movies - 4K DV/10 Cloverfield Lane/2273074-001.png`.  It doesn't pay any attention to whether the two [the one on disk vs. the one coming from Plex] are the same image.  I'll probably add a check to look at the image URL to attempt to ameliorate this at some point.

Script-specific variables in .env:
```
POSTER_DIR=extracted_posters                 # put downloaded posters here
POSTER_DEPTH=20                              # grab this many posters [0 grabs all]
POSTER_DOWNLOAD=0                            # if set to 0, generate a script rather than downloading
POSTER_CONSOLIDATE=1                         # if set to 0, posters are separated into folders by library
```

The point of "POSTER_DEPTH" is that sometimes movies have an insane number of posters, and maybe you don't want all 257 Endgame posters or whatever.  Or maybe you want to download them in batches.

If "POSTER_DOWNLOAD" is `0`, the script will build a shell script for each library to download the images at your convenience instead of downloading them as it runs, so you can run the downloads overnight or on a different machine with ALL THE DISK SPACE or something.

If "POSTER_CONSOLIDATE" is `1`, the script will store all the images in one directory rather than separating them by library name.  The idea is that Plex shows the same set of posters for "Star Wars" whether it's in your "Movies" or "Movies - 4K" or whatever other libraries, so there's no reason to pull the same set of posters multiple times.  There is an example below.

### Usage
1. setup as above
2. Run with `python grab-all-posters.py`

```
tmdb config...
connecting to https://cp1.BING.BANG...
getting items from [Movies - 4K]...
looping over 754 items...
[==================================------] 84.7% ... The Sum of All Fears - 41 posters - 20
```

he posters will be sorted by library [if enabled] with each poster getting an incremented number, like this:

The image names are: `TMDBID-TVDBID-RATINGKEY-INCREMENT.ext`

POSTER_CONSOLIDATE=1:
```
extracted_posters
└── all_libraries
    ├── 100402-Captain America The Winter Soldier
    │   ├── 100402-965-1456628-001.png
    │   ├── 100402-965-1456628-002.png
...
    │   ├── 100402-965-1456628-014.png
    │   └── 100402-965-1456628-015.png
    ├── 10061-Escape from L.A
    │   ├── 10061-2520-1985150-001.png
    │   ├── 10061-2520-1985150-002.png
...
    │   ├── 10061-2520-1985150-014.png
    │   └── 10061-2520-1985150-015.png
...
```

POSTER_CONSOLIDATE=0:
```
extracted_posters
├── Movies - 4K
│   └── 100402-Captain America The Winter Soldier
│       ├── 100402-965-1456628-001.png
│       ├── 100402-965-1456628-002.png
...
│       ├── 100402-965-1456628-014.png
│       └── 100402-965-1456628-015.png
└── Movies - 1080p
    └── 10061-Escape from L.A
        ├── 10061-2520-1985150-001.png
        ├── 10061-2520-1985150-002.png
...
        ├── 10061-2520-1985150-014.png
        └── 10061-2520-1985150-015.png
...
```
## grab-all-status.py

Perhaps you want to move or restore watch status from one server to another [or to a rebuild]

This script will retrieve all watched items for all libraries on a given plex server.  It stores them in a tab-delimited file.

Script-specific variables in .env:
```
PLEX_OWNER=yournamehere                      # account name of the server owner
```

### Usage
1. setup as above
2. Run with `python grab-all-status.py`

```
onnecting to https://cp1.DOMAIN.TLD...
------------ chazlarson ------------
------------ Movies - 4K ------------
chazlarson      movie   Movies - 4K     It Comes at Night       2017    R
chazlarson      movie   Movies - 4K     Mad Max: Fury Road      2015    R
chazlarson      movie   Movies - 4K     Rio     2011    G
chazlarson      movie   Movies - 4K     Rocky   1976    PG
chazlarson      movie   Movies - 4K     The Witch       2015    R
------------ Movies - 4K DV ------------
chazlarson      movie   Movies - 4K DV  It Comes at Night       2017    R
chazlarson      movie   Movies - 4K DV  Mad Max: Fury Road      2015    R
...
```

The file contains one row per user/library/item:

```
chazlarson      movie   Movies - 4K     It Comes at Night       2017    R
chazlarson      movie   Movies - 4K     Mad Max: Fury Road      2015    R
chazlarson      movie   Movies - 4K     Rio     2011    G
chazlarson      movie   Movies - 4K     Rocky   1976    PG
chazlarson      movie   Movies - 4K     The Witch       2015    R
chazlarson      movie   Movies - 4K DV  It Comes at Night       2017    R
chazlarson      movie   Movies - 4K DV  Mad Max: Fury Road      2015    R
...
```

## apply-all-status.py

This script reads the file produces by the previous script and applies the watched status for each user/library/item

Script-specific variables in .env:
```
NONE
```

### Usage
1. setup as above
2. Run with `python apply-all-status.py`

```
connecting to https://cp1.DOMAIN.TLD...

------------ Movies - 4K ------------
Searching for It Comes at Night                                                      Marked watched for chazlarson
...
```

There might be a problem with special characters in titles.
