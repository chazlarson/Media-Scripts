# Plex-Meta Manager scripts

Misc scripts and tools. Undocumented scripts probably do what I need them to but aren't finished yet.

## Setup

1. clone repo
1. Install requirements with `pip install -r requirements.txt` [I'd suggest doing this in a virtual environment]
   Note: the `auth` scripts don't need this step if you run them in the same environment as Plex-Meta Manager itself.
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
1. [extract_collections.py](#extract_collectionspy) - extract collections from a library
1. [pmm_trakt_auth.py](#pmm_trakt_authpy) - generate trakt auth block for PMM config.yml
1. [pmm_mal_auth.py](#pmm_mal_authpy) - generate mal auth block for PMM config.yml

### OBSOLETE
1. [top-n-actor-coll.py](#top-n-actor-collpy) - generate collections for the top *n* actors in a library

## extract_collections.py

You're getting started with Plex-Meta-Manager and you want to export your existing collections

Here is a quick and dirty [emphasis on "quick" and "dirty"] way to do that.

### Usage
1. setup as above
2. Run with `python extract_collections.py`

The script will grab some details from each collection and write a metadata file that you could use with PMM.  It also grabs artwork and background.

This is extremely naive; it doesn't recreate filters, just grabs a list of everything in each collection.

For example, you'll end up with something like this for each collection:

```yaml
collections:
  ABC:
    sort_title: +++_ABC
    url_poster: ./config/TV Shows - 4K-artwork/ABC.png
    summary: A collection of ABC content
    collection_order: release
    plex_search:
      any:
        title:
          - Twin Peaks
          - Strange World
          - Designated Survivor
          - The Good Doctor
```

But it can act as a starting point or recovery backup.

## pmm_trakt_auth.py

Perhaps you're running PMM in a docker or something where getting it into interactive mode to authentication trakt is a hassle.

This little script will generate the trakt section for your PMM config file.  Most of this code is pulled from PMM's own trakt authentication; it's just been simplified to do the one thing.

You can run this on a completely separate machine to where PMM is running.

### Usage
1. setup as above
2. Run with `python pmm_trakt_auth.py`


You'll be asked for your trakt Client ID and Client Secret then taken to a trakt web page.

Copy the PIN and paste it at the prompt.

Some yaml will be printed, ready to copy-paste into your PMM config.yml.

```
Let's authenticate against Trakt!


Trakt Client ID: JOHNNYJOEYDEEDEE
Trakt Client Secret: PETEROGERJOHNKEITH
Taking you to: https://trakt.tv/oauth/authorize?response_type=code&client_id=JOHNNYJOEYDEEDEE&redirect_uri=urn%3Aietf%3Awg%3Aoauth%3A2.0%3Aoob

If you get an OAuth error your Client ID or Client Secret is invalid

If a browser window doesn't open go to that URL manually.


Enter the Trakt pin from that web page: 9CE4045E
Copy the following into your PMM config.yml:
############################################
trakt:
  client_id: JOHNNYJOEYDEEDEE
  client_secret: PETEROGERJOHNKEITH
  authorization:
    access_token: OZZYTONYGEEZERBILL
    token_type: Bearer
    expires_in: 7889237
    refresh_token: JOHNPAULGEORGERINGO
    scope: public
    created_at: 1644589166
############################################
```

## pmm_mal_auth.py

This little script will generate the `mal` section for your PMM config file.  Most of this code is pulled from PMM's own MAL authentication; it's just been simplified to do the one thing.

You can run this on a completely separate machine to where PMM is running.

### Usage
1. setup as above
2. Run with `python pmm_mal_auth.py`


You'll be asked for your MyAnimeList Client ID and Client Secret then taken to a MyAnimeList web page.

Log in and click "Allow"; you'll be redirected to a localhost page that won't load.

Copy that localhost URL and paste it at the prompt.

Some yaml will be printed, ready to copy-paste into your PMM config.yml.

```
Let's authenticate against MyAnimeList!


MyAnimeList Client ID: JOHNNYJOEYDEEDEE
MyAnimeList Client Secret: PETEROGERJOHNKEITH
We're going to open https://myanimelist.net/v1/oauth2/authorize?response_type=code&client_id=JOHNNYJOEYDEEDEE&code_challenge=STINGANDYSTEWART


Log in and click the Allow option.

You will be redirected to a localhost url that probably won't load.

That's fine.  Copy that localhost URL and paste it below.

Hit enter when ready:
URL: http://localhost/?code=TuomasEmppuTroyFloorKaiJukka


Copy the following into your PMM config.yml:
############################################
mal:
  client_id: JOHNNYJOEYDEEDEE
  client_secret: PETEROGERJOHNKEITH
  authorization:
    access_token: OZZYTONYGEEZERBILL
    token_type: Bearer
    expires_in: 2415600
    refresh_token: JOHNPAULGEORGERINGO
############################################

```

## grab-all-posters.py

Perhaps you want to get local copies of some or all the posters Plex knows about for everything in a library.

Maybe you find it easier to look through a bunch of options in CoverFlow or something.

This script will download some or all the posters for every item in a given set of libraries.  It (probably) won't download the same thing more than once, so you can cancel it and restart it if need be.  I say "probably" because the script is assuming that the list of posters retireved from Plex is always in the same order [i.e. that new posters get appended to the end of the list].  On subsequent runs, the script checks only that a file exists at, for example, `extracted_posters/all_libraries/578-Jaws/578-829-1452479-015.png`.  It doesn't pay any attention to whether the two [the one on disk vs. the one coming from Plex] are the same image.  I'll probably add a check to look at the image URL to attempt to ameliorate this at some point.

Script-specific variables in .env:
```
POSTER_DIR=extracted_posters                 # put downloaded posters here
POSTER_DEPTH=20                              # grab this many posters [0 grabs all]
POSTER_DOWNLOAD=0                            # if set to 0, generate a script rather than downloading
POSTER_CONSOLIDATE=1                         # if set to 0, posters are separated into folders by library
```

The point of "POSTER_DEPTH" is that sometimes movies have an insane number of posters, and maybe you don't want all 257 Endgame posters or whatever.  Or maybe you want to download them in batches.

If "POSTER_DOWNLOAD" is `0`, the script will build a shell script for each library to download the images at your convenience instead of downloading them as it runs, so you can run the downloads overnight or on a different machine with ALL THE DISK SPACE or something.

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

The posters will be sorted by library [if enabled] with each poster getting an incremented number, like this:

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
connecting to https://cp1.DOMAIN.TLD...
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

## grab-all-posters.py

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

## OBSOLETE SCRIPTS

## top-n-actor-coll.py

This has been obsoleted by "Dynamic Collections" in PMM; it's left here for historical reference.

You should use Dynamic Collections instead.

Connects to a plex library, grabs all the movies.

For each movie, gets the cast from TMDB; keeps track across all movies how many times it sees each actor.  You can specify a TV library, but I haven't tested that a lot.  My one attempt showed a list of 10 actors who had each been in 1 series, which doesn't seem right.

At the end, builds a basic Plex-Meta-Manager metadata file for the top N actors.

Script-specific variables in .env:
```
CAST_DEPTH=20                   ### HOW DEEP TO GO INTO EACH MOVIE CAST
TOP_COUNT=10                    ### PUT THIS MANY INTO THE FILE AT THE END
```

`CAST_DEPTH` is meant to prevent some journeyman character actor from showing up in the top ten; I'm thinking of someone like Clint Howard who's been in the cast of many movies, but I'm guessing when you think of the top ten actors in your library you're not thinking about Clint.  Maybe you are, though, in which case set that higher.

`TOP_COUNT` is the number of actors to dump into the metadata file at the end.

`template.tmpl` - this is the beginning of the target metadata file; change it if you like, but you're on your own there.

`collection.tmpl` - this is the collection definition inserted for each actor [`%%NAME%%%` and `%%ID%%` are placeholders that get substituted for each actor]; change it if you like, but this script only knows about those two data field substitutions.

### Usage
1. setup as above
1. Run with `python top-n-actor-coll.py`

```
connecting...
getting movies...
looping over 2819 movies...
[==--------------------------------------] 5.4% ... Annihilation
```

It will go through all your movies, and then at the end print out however many actors you specified in TOP_COUNT and produce a yml file.

```
38      2231-Samuel L. Jackson
26      500-Tom Cruise
25      64-Gary Oldman
25      192-Morgan Freeman
23      884-Steve Buscemi
22      62-Bruce Willis
22      31-Tom Hanks
21      19278-Bill Hader
21      2888-Will Smith
21      16483-Sylvester Stallone
```

In my 4K movie library, the script produces:

```
######################################################
#               People Collections                   #
######################################################
templates:
  Person:
    smart_filter:
      any:
        actor: tmdb
        director: tmdb
        writer: tmdb
        producer: tmdb
      sort_by: year.asc
      validate: false
    tmdb_person: <<person>>
    sort_title: +9_<<collection_name>>
    schedule: weekly(monday)
    collection_order: release
    collection_mode: hide

collections:
  Samuel L. Jackson:
    template: {name: Person, person: 2231}
  Tom Cruise:
    template: {name: Person, person: 500}
  Gary Oldman:
    template: {name: Person, person: 64}
  Morgan Freeman:
    template: {name: Person, person: 192}
  Steve Buscemi:
    template: {name: Person, person: 884}
  Bruce Willis:
    template: {name: Person, person: 62}
  Tom Hanks:
    template: {name: Person, person: 31}
  Bill Hader:
    template: {name: Person, person: 19278}
  Will Smith:
    template: {name: Person, person: 2888}
  Sylvester Stallone:
    template: {name: Person, person: 16483}
```
